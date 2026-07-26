"""Composition root: assembles the object graph for the CLI.

This is the only module in the codebase allowed to import concrete adapters
and construct concrete use cases directly. cli.py calls these factory
functions instead of constructing anything itself, so every other module can
depend on abstract ports (use_cases/ports/) without knowing which concrete
adapter ultimately gets wired in.
"""

from __future__ import annotations

from adapters.csv_result_writer import CsvResultWriter
from adapters.directory_request_discovery import DirectoryRequestDiscovery
from adapters.json_data_loader import JsonDataLoader
from adapters.json_result_writer import JsonResultWriter
from adapters.json_solution_loader import JsonSolutionLoader
from settings import Settings
from use_cases.ports.base_request_discovery import BaseRequestDiscovery
from use_cases.ports.base_result_writer import BaseResultWriter
from use_cases.solving.optimization.heuristic.greedy_calories import GreedyCalories
from use_cases.solving.optimization.mip.mip_strategy import MipStrategy
from use_cases.solving.optimization.mip.optimization.optimization import Optimization
from use_cases.solving.optimization.mip.optimization.solvers.base_technology_solver import BaseTechnologySolver
from use_cases.solving.optimization.mip.optimization.solvers.highs_solver import HighsSolver
from use_cases.solving.orchestrator import Orchestrator
from use_cases.solving.postprocessing.postprocessing import PostProcess
from use_cases.solving.preprocessing.preprocessing import PreProcess
from use_cases.use_case_evaluate_solution_for_request import EvaluateSolutionForRequest
from use_cases.use_case_solve_multiple_requests import SolveMultipleRequests
from use_cases.use_case_solve_single_request import SolveSingleRequest


def build_solver(settings: Settings) -> BaseTechnologySolver:
    """Resolve settings.solver_name to a concrete BaseTechnologySolver.

    This is the one place in the codebase where a solver name string is
    mapped to a class. Adding a new solver means adding one more branch here
    and a new BaseTechnologySolver subclass — nothing else in the codebase
    needs to change.

    Args:
        settings: Application settings; only solver_name is used.

    Returns:
        The solver instance matching settings.solver_name.

    Raises:
        ValueError: If settings.solver_name does not match a known solver.
    """
    if settings.solver_name == "highs":
        return HighsSolver()
    raise ValueError(f"Unknown solver '{settings.solver_name}'. Available: ['highs']")


def build_orchestrator(settings: Settings) -> Orchestrator:
    """Assemble an Orchestrator with all of its solving-pipeline collaborators.

    Args:
        settings: Application settings; forwarded to build_solver() to pick
            the MIP solver technology.

    Returns:
        A fully wired Orchestrator, ready to solve a Request.
    """
    optimization = Optimization(solver=build_solver(settings))
    return Orchestrator(
        preprocessing=PreProcess(),
        postprocessing=PostProcess(),
        mip_strategy=MipStrategy(optimization=optimization),
        heuristic_strategy=GreedyCalories(),
    )


def build_solve_single_request(settings: Settings, folder_path: str | None = None) -> SolveSingleRequest:
    """Assemble a SolveSingleRequest use case.

    Args:
        settings: Application settings; solver_name is forwarded to
            build_orchestrator().
        folder_path: Folder to load request data from. Defaults to
            settings.folder_path when omitted, so a caller solving a batch
            from a different folder (SolveMultipleRequests) can point this
            use case elsewhere without touching Settings.

    Returns:
        A fully wired SolveSingleRequest, ready to solve one request ID.
    """
    return SolveSingleRequest(
        request_loader=JsonDataLoader(folder_path=folder_path or settings.folder_path),
        orchestrator=build_orchestrator(settings),
    )


def build_request_discovery(folder_path: str) -> BaseRequestDiscovery:
    """Assemble a BaseRequestDiscovery scanning folder_path for requests.

    Args:
        folder_path: Root folder to scan for request subfolders.

    Returns:
        A DirectoryRequestDiscovery over folder_path.
    """
    return DirectoryRequestDiscovery(folder_path=folder_path)


def build_solve_multiple_requests(settings: Settings, folder_path: str) -> SolveMultipleRequests:
    """Assemble a SolveMultipleRequests use case scanning folder_path for requests.

    Args:
        settings: Application settings; solver_name is forwarded to
            build_orchestrator().
        folder_path: Root folder to scan for request subfolders, and the
            same folder each discovered request is loaded from.

    Returns:
        A fully wired SolveMultipleRequests, ready to solve every request
        folder_path contains.
    """
    return SolveMultipleRequests(
        request_discovery=build_request_discovery(folder_path),
        solve_single_request=build_solve_single_request(settings, folder_path=folder_path),
    )


def build_evaluate_solution_for_request(
    settings: Settings, folder_path: str | None = None
) -> EvaluateSolutionForRequest:
    """Assemble an EvaluateSolutionForRequest use case.

    Args:
        settings: Application settings.
        folder_path: Folder to load request data from. Defaults to
            settings.folder_path when omitted.

    Returns:
        A fully wired EvaluateSolutionForRequest, ready to evaluate a
        candidate solution against one request ID.
    """
    return EvaluateSolutionForRequest(
        request_loader=JsonDataLoader(folder_path=folder_path or settings.folder_path),
        solution_loader=JsonSolutionLoader(),
    )


def build_result_writer(settings: Settings, format_: str = "csv") -> BaseResultWriter:
    """Select the concrete BaseResultWriter matching the requested output format.

    Args:
        settings: Application settings; output_folder_path is where the
            writer persists each run.
        format_: Either "csv" or "json"; selects which concrete writer to build.

    Returns:
        The writer instance matching format_.

    Raises:
        ValueError: If format_ is neither "csv" nor "json".
    """
    if format_ == "csv":
        return CsvResultWriter(output_folder_path=settings.output_folder_path)
    if format_ == "json":
        return JsonResultWriter(output_folder_path=settings.output_folder_path)
    raise ValueError(f"Unknown format '{format_}'. Available: ['csv', 'json']")
