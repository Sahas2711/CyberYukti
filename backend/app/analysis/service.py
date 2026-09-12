"""Analysis service for GitHub + DockerHub security analysis pipeline."""

import asyncio
import json
import os
import shutil
import subprocess
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.app.analysis.models import (
    AnalysisArtifacts,
    AnalysisMetadata,
    AnalysisStatus,
    CanonicalFindingResponse,
    DockerAcquisition,
    DockerImageInfo,
    GitHubAcquisition,
    GitHubRepoInfo,
    PipelineProcessing,
    ScannerExecution,
    ScannerStatus,
    create_analysis_id,
    get_analysis_dir,
)
from backend.app.ingestion.normalizer import FindingIntelligenceEngine
from backend.app.ingestion.models import CanonicalFinding, IncidentCluster, IngestionSummary
from backend.app.ingestion.parsers.semgrep_parser import SemgrepParser
from backend.app.ingestion.parsers.trivy_parser import TrivyParser


class AnalysisService:
    """Orchestrates the complete GitHub + DockerHub analysis pipeline."""

    def __init__(self, max_concurrent: int = 2):
        self.max_concurrent = max_concurrent
        self._running: Dict[str, AnalysisMetadata] = {}
        self.engine = FindingIntelligenceEngine()

    @staticmethod
    def _tool_available(tool: str) -> bool:
        """True when the scanner binary exists and is executable on PATH."""
        return shutil.which(tool) is not None

    async def create_analysis(
        self,
        github_url: Optional[str],
        dockerhub_image: Optional[str],
        authorization: bool,
    ) -> AnalysisMetadata:
        """Create a new analysis job."""
        if not authorization:
            raise ValueError("Authorization is required")

        if not github_url and not dockerhub_image:
            raise ValueError("At least one of github_url or dockerhub_image must be provided")

        analysis_id = create_analysis_id()
        analysis_dir = get_analysis_dir(analysis_id)
        analysis_dir.mkdir(parents=True, exist_ok=True)

        metadata = AnalysisMetadata(
            analysis_id=analysis_id,
            status=AnalysisStatus.QUEUED,
            github_url=github_url,
            dockerhub_image=dockerhub_image,
            authorization=authorization,
            artifacts=AnalysisArtifacts(),
        )

        # Save initial metadata
        await self._save_metadata(metadata, analysis_dir)

        # Start background processing
        asyncio.create_task(self._run_analysis(analysis_id, metadata, analysis_dir))

        return metadata

    async def get_analysis(self, analysis_id: str) -> Optional[AnalysisMetadata]:
        """Get analysis metadata by ID."""
        if analysis_id in self._running:
            return self._running[analysis_id]

        analysis_dir = get_analysis_dir(analysis_id)
        metadata_path = analysis_dir / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                data = json.load(f)
            return AnalysisMetadata(**data)
        return None

    async def get_analysis_logs(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed logs for an analysis."""
        metadata = await self.get_analysis(analysis_id)
        if not metadata:
            return None

        return {
            "analysis_id": analysis_id,
            "github_acquisition": metadata.github,
            "semgrep": metadata.semgrep,
            "docker_pull": metadata.docker,
            "trivy": metadata.trivy,
            "pipeline": metadata.pipeline,
        }

    async def get_analysis_findings(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get normalized findings for an analysis."""
        metadata = await self.get_analysis(analysis_id)
        if not metadata or not metadata.artifacts or not metadata.artifacts.canonical_findings_path:
            return None

        findings_path = Path(metadata.artifacts.canonical_findings_path)
        if not findings_path.exists():
            return None

        with open(findings_path, "r") as f:
            data = json.load(f)

        return {
            "analysis_id": analysis_id,
            "total_findings": data.get("total", 0),
            "semgrep_findings": data.get("semgrep", 0),
            "trivy_findings": data.get("trivy", 0),
            "findings": data.get("findings", []),
        }

    async def get_analysis_clusters(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get incident clusters for an analysis."""
        metadata = await self.get_analysis(analysis_id)
        if not metadata or not metadata.artifacts or not metadata.artifacts.incident_clusters_path:
            return None

        clusters_path = Path(metadata.artifacts.incident_clusters_path)
        if not clusters_path.exists():
            return None

        with open(clusters_path, "r") as f:
            data = json.load(f)

        return {
            "analysis_id": analysis_id,
            "total_clusters": data.get("total_clusters", 0),
            "clusters": data.get("clusters", []),
        }

    async def get_analysis_report(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get complete analysis report."""
        metadata = await self.get_analysis(analysis_id)
        if not metadata:
            return None

        # Load all artifacts
        artifacts = {}
        if metadata.artifacts:
            for field_name, field_value in metadata.artifacts.__dict__.items():
                if field_value and Path(field_value).exists():
                    with open(field_value, "r") as f:
                        artifacts[field_name] = json.load(f)

        return {
            "analysis_id": analysis_id,
            "metadata": metadata.model_dump(),
            "summary": artifacts.get("analysis_summary", {}),
            "scanner_summary": {
                "semgrep": metadata.semgrep.model_dump() if metadata.semgrep else {},
                "trivy": metadata.trivy.model_dump() if metadata.trivy else {},
            },
            "finding_summary": artifacts.get("canonical_findings", {}),
            "deduplication_summary": artifacts.get("deduplication", {}),
            "correlation_summary": artifacts.get("correlations", {}),
            "incident_clusters": artifacts.get("incident_clusters", {}).get("clusters", []),
        }

    async def _run_analysis(
        self,
        analysis_id: str,
        metadata: AnalysisMetadata,
        analysis_dir: Path,
    ) -> None:
        """Run the complete analysis pipeline."""
        self._running[analysis_id] = metadata
        metadata.status = AnalysisStatus.RUNNING
        metadata.started_at = datetime.utcnow()
        await self._save_metadata(metadata, analysis_dir)

        try:
            # Create subdirectories
            github_dir = analysis_dir / "github"
            semgrep_dir = analysis_dir / "semgrep"
            docker_dir = analysis_dir / "docker"
            trivy_dir = analysis_dir / "trivy"
            cyberyukti_dir = analysis_dir / "cyberyukti"
            for d in [github_dir, semgrep_dir, docker_dir, trivy_dir, cyberyukti_dir]:
                d.mkdir(parents=True, exist_ok=True)

            repo_path = None
            image_ref = None
            skipped_scanners: List[str] = []

            # Phase 1: GitHub acquisition
            if metadata.github_url:
                metadata.status = AnalysisStatus.GITHUB_CLONE
                await self._save_metadata(metadata, analysis_dir)
                repo_path, github_info = await self._clone_github_repo(
                    str(metadata.github_url), github_dir, metadata
                )
                metadata.github.repository = github_info

            # Phase 2: Semgrep scan (skipped gracefully if semgrep is not
            # installed — the analysis continues with whatever sources remain)
            if repo_path:
                if self._tool_available("semgrep"):
                    metadata.status = AnalysisStatus.SEMGREP_SCAN
                    await self._save_metadata(metadata, analysis_dir)
                    await self._run_semgrep(repo_path, semgrep_dir, metadata)
                else:
                    metadata.semgrep = ScannerExecution(
                        scanner="semgrep",
                        status=ScannerStatus.SKIPPED,
                        error="semgrep is not installed or not on PATH; scan skipped",
                    )
                    skipped_scanners.append("semgrep")

            # Phase 3: Docker image pull
            if metadata.dockerhub_image:
                metadata.status = AnalysisStatus.DOCKER_PULL
                await self._save_metadata(metadata, analysis_dir)
                image_ref, docker_info = await self._pull_docker_image(
                    str(metadata.dockerhub_image), docker_dir, metadata
                )
                metadata.docker.image = docker_info

            # Phase 4: Trivy scan (skipped gracefully if trivy is not installed)
            if image_ref:
                if self._tool_available("trivy"):
                    metadata.status = AnalysisStatus.TRIVY_SCAN
                    await self._save_metadata(metadata, analysis_dir)
                    await self._run_trivy(image_ref, trivy_dir, metadata)
                else:
                    metadata.trivy = ScannerExecution(
                        scanner="trivy",
                        status=ScannerStatus.SKIPPED,
                        error="trivy is not installed or not on PATH; scan skipped",
                    )
                    skipped_scanners.append("trivy")

            # Phase 5: CyberYukti pipeline processing
            metadata.status = AnalysisStatus.NORMALIZING
            await self._save_metadata(metadata, analysis_dir)
            await self._process_pipeline(
                analysis_id,
                semgrep_dir if repo_path else None,
                trivy_dir if image_ref else None,
                cyberyukti_dir,
                metadata,
                analysis_dir,
            )

            # PARTIAL when at least one requested scanner could not run
            if skipped_scanners:
                metadata.status = AnalysisStatus.PARTIAL
                metadata.partial_results = True
                metadata.error = "Skipped: " + ", ".join(skipped_scanners)
            else:
                metadata.status = AnalysisStatus.COMPLETED
            metadata.completed_at = datetime.utcnow()
            if metadata.started_at:
                metadata.duration_seconds = (metadata.completed_at - metadata.started_at).total_seconds()

        except Exception as e:
            metadata.status = AnalysisStatus.FAILED
            metadata.error = str(e)
            metadata.completed_at = datetime.utcnow()
            if metadata.started_at:
                metadata.duration_seconds = (metadata.completed_at - metadata.started_at).total_seconds()

        finally:
            await self._save_metadata(metadata, analysis_dir)
            self._running.pop(analysis_id, None)

    async def _clone_github_repo(
        self, github_url: str, github_dir: Path, metadata: AnalysisMetadata
    ) -> Tuple[Path, GitHubRepoInfo]:
        """Clone GitHub repository and return local path and repo info."""
        acquisition = GitHubAcquisition()
        metadata.github = acquisition

        start_time = datetime.utcnow()
        acquisition.start_time = start_time

        # Parse URL
        url = github_url.rstrip("/")
        if url.endswith(".git"):
            url = url[:-4]
        parts = url.split("/")
        owner = parts[-2]
        name = parts[-1]
        full_name = f"{owner}/{name}"

        # Create temp directory for clone
        repo_path = github_dir / "repo"
        if repo_path.exists():
            shutil.rmtree(repo_path)

        # Clone command
        clone_cmd = [
            "git",
            "clone",
            "--depth",
            "1",
            github_url,
            str(repo_path),
        ]
        acquisition.clone_command = clone_cmd

        try:
            proc = await asyncio.create_subprocess_exec(
                *clone_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(github_dir),
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
            acquisition.stdout = stdout.decode("utf-8", errors="replace")
            acquisition.stderr = stderr.decode("utf-8", errors="replace")
            acquisition.exit_code = proc.returncode

            if proc.returncode != 0:
                raise RuntimeError(f"Git clone failed: {acquisition.stderr}")

            # Get commit SHA
            sha_proc = await asyncio.create_subprocess_exec(
                "git", "rev-parse", "HEAD",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(repo_path),
            )
            sha_stdout, _ = await sha_proc.communicate()
            commit_sha = sha_stdout.decode("utf-8", errors="replace").strip() if sha_proc.returncode == 0 else None

            # Get default branch
            branch_proc = await asyncio.create_subprocess_exec(
                "git", "symbolic-ref", "--short", "HEAD",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(repo_path),
            )
            branch_stdout, _ = await branch_proc.communicate()
            branch = branch_stdout.decode("utf-8", errors="replace").strip() if branch_proc.returncode == 0 else None

            # Calculate repo size
            size_kb = sum(f.stat().st_size for f in repo_path.rglob("*") if f.is_file()) // 1024

            end_time = datetime.utcnow()
            acquisition.end_time = end_time
            acquisition.duration_seconds = (end_time - start_time).total_seconds()

            github_info = GitHubRepoInfo(
                url=github_url,
                owner=owner,
                name=name,
                full_name=full_name,
                commit_sha=commit_sha,
                branch=branch,
                size_kb=size_kb,
            )

            # Save acquisition log
            acq_path = github_dir / "acquisition.json"
            with open(acq_path, "w") as f:
                json.dump(acquisition.model_dump(), f, indent=2, default=str)
            metadata.artifacts.github_acquisition_path = str(acq_path)

            # Save repository info
            repo_info_path = github_dir / "repository.json"
            with open(repo_info_path, "w") as f:
                json.dump(github_info.model_dump(), f, indent=2, default=str)

            return repo_path, github_info

        except asyncio.TimeoutError:
            acquisition.error = "Git clone timed out after 300 seconds"
            acquisition.exit_code = -1
            raise
        except Exception as e:
            acquisition.error = str(e)
            raise

    async def _run_semgrep(self, repo_path: Path, semgrep_dir: Path, metadata: AnalysisMetadata) -> None:
        """Run Semgrep SAST scan on the repository."""
        execution = ScannerExecution(scanner="semgrep")
        metadata.semgrep = execution

        start_time = datetime.utcnow()
        execution.start_time = start_time

        # Get semgrep version
        try:
            version_proc = await asyncio.create_subprocess_exec(
                "semgrep", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            version_stdout, _ = await version_proc.communicate()
            execution.version = version_stdout.decode("utf-8", errors="replace").strip()
        except Exception:
            execution.version = "unknown"

        # Run semgrep with JSON output
        cmd = [
            "semgrep",
            "scan",
            "--json",
            "--config=auto",
            "--no-git-ignore",
            str(repo_path),
        ]
        execution.command = cmd

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(repo_path),
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=600)
            execution.stdout = stdout.decode("utf-8", errors="replace")
            execution.stderr = stderr.decode("utf-8", errors="replace")
            execution.exit_code = proc.returncode

            # Save raw outputs
            stdout_path = semgrep_dir / "stdout.log"
            stderr_path = semgrep_dir / "stderr.log"
            raw_path = semgrep_dir / "raw-results.json"

            with open(stdout_path, "w") as f:
                f.write(execution.stdout)
            with open(stderr_path, "w") as f:
                f.write(execution.stderr)

            # Parse and save raw JSON
            try:
                raw_json = json.loads(execution.stdout)
                with open(raw_path, "w") as f:
                    json.dump(raw_json, f, indent=2)
                # Count findings
                results = raw_json.get("results", [])
                execution.findings_count = len(results)
            except json.JSONDecodeError:
                execution.findings_count = 0

            execution.raw_output_path = str(raw_path)
            metadata.artifacts.semgrep_stdout_path = str(stdout_path)
            metadata.artifacts.semgrep_stderr_path = str(stderr_path)
            metadata.artifacts.semgrep_raw_path = str(raw_path)

        except asyncio.TimeoutError:
            execution.error = "Semgrep scan timed out after 600 seconds"
            execution.exit_code = -1
            execution.status = ScannerStatus.FAILED
            raise
        except Exception as e:
            execution.error = str(e)
            execution.status = ScannerStatus.FAILED
            raise
        finally:
            end_time = datetime.utcnow()
            execution.end_time = end_time
            execution.duration_seconds = (end_time - start_time).total_seconds()
            if execution.exit_code == 0:
                execution.status = ScannerStatus.COMPLETED
            else:
                execution.status = ScannerStatus.FAILED

    async def _pull_docker_image(
        self, image_ref: str, docker_dir: Path, metadata: AnalysisMetadata
    ) -> Tuple[str, DockerImageInfo]:
        """Pull Docker image and return image reference and info."""
        acquisition = DockerAcquisition()
        metadata.docker = acquisition

        start_time = datetime.utcnow()
        acquisition.start_time = start_time

        # Normalize image reference
        if image_ref.startswith("https://hub.docker.com/r/"):
            parts = image_ref.rstrip("/").split("/")
            image_ref = f"{parts[-2]}/{parts[-1]}"
        if ":" not in image_ref:
            image_ref = f"{image_ref}:latest"

        pull_cmd = ["docker", "pull", image_ref]
        acquisition.pull_command = pull_cmd

        try:
            proc = await asyncio.create_subprocess_exec(
                *pull_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
            acquisition.stdout = stdout.decode("utf-8", errors="replace")
            acquisition.stderr = stderr.decode("utf-8", errors="replace")
            acquisition.exit_code = proc.returncode

            if proc.returncode != 0:
                raise RuntimeError(f"Docker pull failed: {acquisition.stderr}")

            # Get image info
            inspect_cmd = ["docker", "inspect", image_ref]
            inspect_proc = await asyncio.create_subprocess_exec(
                *inspect_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            inspect_stdout, _ = await inspect_proc.communicate()
            if inspect_proc.returncode == 0:
                inspect_data = json.loads(inspect_stdout.decode("utf-8"))[0]
                repo_tag = image_ref.split(":")[0]
                tag = image_ref.split(":")[1] if ":" in image_ref else "latest"
                digest = inspect_data.get("RepoDigests", [None])[0]
                size = inspect_data.get("Size", 0)
                arch = inspect_data.get("Architecture")
                os = inspect_data.get("Os")

                docker_info = DockerImageInfo(
                    image_ref=image_ref,
                    repository=repo_tag,
                    tag=tag,
                    digest=digest,
                    size_bytes=size,
                    architecture=arch,
                    os=os,
                )
            else:
                docker_info = DockerImageInfo(
                    image_ref=image_ref,
                    repository=image_ref.split(":")[0],
                    tag=image_ref.split(":")[1] if ":" in image_ref else "latest",
                )

            end_time = datetime.utcnow()
            acquisition.end_time = end_time
            acquisition.duration_seconds = (end_time - start_time).total_seconds()

            # Save acquisition log
            pull_path = docker_dir / "pull.log"
            with open(pull_path, "w") as f:
                f.write(acquisition.stdout)
            metadata.artifacts.docker_pull_path = str(pull_path)

            # Save image info
            image_info_path = docker_dir / "image.json"
            with open(image_info_path, "w") as f:
                json.dump(docker_info.model_dump(), f, indent=2, default=str)

            return image_ref, docker_info

        except asyncio.TimeoutError:
            acquisition.error = "Docker pull timed out after 300 seconds"
            acquisition.exit_code = -1
            raise
        except Exception as e:
            acquisition.error = str(e)
            raise

    async def _run_trivy(self, image_ref: str, trivy_dir: Path, metadata: AnalysisMetadata) -> None:
        """Run Trivy scan on the Docker image."""
        execution = ScannerExecution(scanner="trivy")
        metadata.trivy = execution

        start_time = datetime.utcnow()
        execution.start_time = start_time

        # Get trivy version
        try:
            version_proc = await asyncio.create_subprocess_exec(
                "trivy", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            version_stdout, _ = await version_proc.communicate()
            execution.version = version_stdout.decode("utf-8", errors="replace").strip()
        except Exception:
            execution.version = "unknown"

        # Run trivy with JSON output
        cmd = [
            "trivy",
            "image",
            "--format", "json",
            "--scanners", "vuln,secret,config",
            image_ref,
        ]
        execution.command = cmd

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=600)
            execution.stdout = stdout.decode("utf-8", errors="replace")
            execution.stderr = stderr.decode("utf-8", errors="replace")
            execution.exit_code = proc.returncode

            # Save raw outputs
            stdout_path = trivy_dir / "stdout.log"
            stderr_path = trivy_dir / "stderr.log"
            raw_path = trivy_dir / "raw-results.json"

            with open(stdout_path, "w") as f:
                f.write(execution.stdout)
            with open(stderr_path, "w") as f:
                f.write(execution.stderr)

            # Parse and save raw JSON
            try:
                raw_json = json.loads(execution.stdout)
                with open(raw_path, "w") as f:
                    json.dump(raw_json, f, indent=2)
                # Count findings
                findings_count = 0
                for result in raw_json.get("Results", []):
                    vulns = result.get("Vulnerabilities", [])
                    findings_count += len(vulns)
                execution.findings_count = findings_count
            except json.JSONDecodeError:
                execution.findings_count = 0

            execution.raw_output_path = str(raw_path)
            metadata.artifacts.trivy_stdout_path = str(stdout_path)
            metadata.artifacts.trivy_stderr_path = str(stderr_path)
            metadata.artifacts.trivy_raw_path = str(raw_path)

        except asyncio.TimeoutError:
            execution.error = "Trivy scan timed out after 600 seconds"
            execution.exit_code = -1
            execution.status = ScannerStatus.FAILED
            raise
        except Exception as e:
            execution.error = str(e)
            execution.status = ScannerStatus.FAILED
            raise
        finally:
            end_time = datetime.utcnow()
            execution.end_time = end_time
            execution.duration_seconds = (end_time - start_time).total_seconds()
            if execution.exit_code == 0:
                execution.status = ScannerStatus.COMPLETED
            else:
                execution.status = ScannerStatus.FAILED

    async def _process_pipeline(
        self,
        analysis_id: str,
        semgrep_dir: Optional[Path],
        trivy_dir: Optional[Path],
        cyberyukti_dir: Path,
        metadata: AnalysisMetadata,
        analysis_dir: Path,
    ) -> None:
        """Process findings through CyberYukti pipeline."""
        pipeline = PipelineProcessing()
        metadata.pipeline = pipeline

        start_time = datetime.utcnow()
        pipeline.start_time = start_time

        all_findings: List[CanonicalFinding] = []
        semgrep_count = 0
        trivy_count = 0

        # Parse Semgrep results
        if semgrep_dir and metadata.artifacts and metadata.artifacts.semgrep_raw_path:
            raw_path = Path(metadata.artifacts.semgrep_raw_path)
            if raw_path.exists():
                with open(raw_path, "r") as f:
                    raw_data = json.load(f)
                findings = SemgrepParser.parse_dict(raw_data, default_asset=f"analysis-{analysis_id}")
                all_findings.extend(findings)
                semgrep_count = len(findings)

        # Parse Trivy results
        if trivy_dir and metadata.artifacts and metadata.artifacts.trivy_raw_path:
            raw_path = Path(metadata.artifacts.trivy_raw_path)
            if raw_path.exists():
                with open(raw_path, "r") as f:
                    raw_data = json.load(f)
                findings = TrivyParser.parse_dict(raw_data, default_asset=f"analysis-{analysis_id}")
                all_findings.extend(findings)
                trivy_count = len(findings)

        pipeline.canonical_findings_count = len(all_findings)

        # Save canonical findings
        canonical_path = cyberyukti_dir / "canonical-findings.json"
        canonical_data = {
            "total": len(all_findings),
            "semgrep": semgrep_count,
            "trivy": trivy_count,
            "findings": [f.model_dump() for f in all_findings],
        }
        with open(canonical_path, "w") as f:
            json.dump(canonical_data, f, indent=2, default=str)
        metadata.artifacts.canonical_findings_path = str(canonical_path)

        # Run deduplication and correlation (also runs on an empty finding
        # list so the artifacts/endpoints always exist with consistent shapes)
        metadata.status = AnalysisStatus.DEDUPLICATING
        await self._save_metadata(metadata, analysis_dir)

        clusters, summary = self.engine.process_findings(all_findings)

        pipeline.incident_clusters_created = len(clusters)
        total_collapsed = summary.total_raw_findings - len(clusters)
        # The engine collapses findings through exact-hash dedup AND
        # triple-tuple clustering; we can't split the two stages from the
        # summary alone, so report the combined number as exact duplicates
        # removed and leave the triple-tuple field at zero (documented
        # limitation) rather than double-counting.
        pipeline.exact_duplicates_removed = max(total_collapsed, 0)

        # Save deduplication results
        dedup_path = cyberyukti_dir / "deduplication.json"
        with open(dedup_path, "w") as f:
            json.dump(summary.model_dump(), f, indent=2, default=str)
        metadata.artifacts.deduplication_path = str(dedup_path)

        # Save clusters
        clusters_path = cyberyukti_dir / "incident-clusters.json"
        clusters_data = {
            "total_clusters": len(clusters),
            "clusters": [c.model_dump() for c in clusters],
        }
        with open(clusters_path, "w") as f:
            json.dump(clusters_data, f, indent=2, default=str)
        metadata.artifacts.incident_clusters_path = str(clusters_path)

        # Save correlations (placeholder - would need more detailed correlation data)
        corr_path = cyberyukti_dir / "correlations.json"
        with open(corr_path, "w") as f:
            json.dump({
                "cross_tool_correlations": len([c for c in clusters if len(c.participating_tools) > 1]),
                "clusters_by_tool": {tool: len([c for c in clusters if tool in c.participating_tools])
                                     for tool in ["semgrep", "trivy"]},
            }, f, indent=2)
        metadata.artifacts.correlations_path = str(corr_path)

        # Save analysis summary
        summary_path = cyberyukti_dir / "analysis-summary.json"
        with open(summary_path, "w") as f:
            json.dump({
                "total_raw_findings": summary.total_raw_findings,
                "total_clusters": summary.total_clusters,
                "noise_reduction_percentage": summary.noise_reduction_percentage,
                "breakdown_by_tool": summary.breakdown_by_tool,
            }, f, indent=2, default=str)
        metadata.artifacts.analysis_summary_path = str(summary_path)

        # Save final report
        report_path = cyberyukti_dir / "final-report.json"
        with open(report_path, "w") as f:
            json.dump({
                "analysis_id": analysis_id,
                "status": metadata.status.value,
                "github_url": str(metadata.github_url) if metadata.github_url else None,
                "dockerhub_image": metadata.dockerhub_image,
                "semgrep_findings": semgrep_count,
                "trivy_findings": trivy_count,
                "total_findings": len(all_findings),
                "incident_clusters": pipeline.incident_clusters_created,
                "duration_seconds": metadata.duration_seconds,
            }, f, indent=2, default=str)
        metadata.artifacts.final_report_path = str(report_path)

        end_time = datetime.utcnow()
        pipeline.end_time = end_time
        pipeline.duration_seconds = (end_time - start_time).total_seconds()

    async def _save_metadata(self, metadata: AnalysisMetadata, analysis_dir: Path) -> None:
        """Save metadata to disk."""
        metadata_path = analysis_dir / "metadata.json"
        if metadata.artifacts:
            metadata.artifacts.metadata_path = str(metadata_path)
        with open(metadata_path, "w") as f:
            json.dump(metadata.model_dump(), f, indent=2, default=str)


# Global instance
analysis_service = AnalysisService()