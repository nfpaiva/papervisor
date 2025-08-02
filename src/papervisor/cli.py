"""Command line interface for papervisor."""

import argparse
import sys

from .core import Papervisor


def main() -> None:
    """Main entry point for the papervisor CLI."""
    parser = argparse.ArgumentParser(
        description="Papervisor: Literature Review Pipeline"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List projects command
    projects_parser = subparsers.add_parser(
        "list-projects", help="List all literature review projects"
    )
    projects_parser.add_argument(
        "--data-dir", default="data", help="Data directory path"
    )

    # List queries command
    list_parser = subparsers.add_parser(
        "list-queries", help="List search queries for a project"
    )
    list_parser.add_argument("project_id", help="Project ID to list queries for")
    list_parser.add_argument("--data-dir", default="data", help="Data directory path")

    # Load query command
    load_parser = subparsers.add_parser(
        "load-query", help="Load results for a specific query"
    )
    load_parser.add_argument("project_id", help="Project ID")
    load_parser.add_argument("query_id", help="Query ID to load")
    load_parser.add_argument("--data-dir", default="data", help="Data directory path")
    load_parser.add_argument("--stats", action="store_true", help="Show statistics")

    # Statistics command
    stats_parser = subparsers.add_parser(
        "stats", help="Show statistics for query results"
    )
    stats_parser.add_argument("project_id", help="Project ID")
    stats_parser.add_argument(
        "query_id",
        nargs="?",
        help="Query ID (if not provided, shows combined project stats)",
    )
    stats_parser.add_argument("--data-dir", default="data", help="Data directory path")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        papervisor = Papervisor(args.data_dir)

        if args.command == "list-projects":
            projects = papervisor.list_projects()
            if not projects:
                print("No literature review projects found.")
                return

            print(f"Found {len(projects)} literature review projects:")
            for project in projects:
                print(f"  - {project.project_id}: {project.title}")
                print(f"    Description: {project.description}")
                print(f"    Status: {project.status}")
                print(f"    Lead: {project.lead_researcher}")
                print(f"    Created: {project.created_date}")
                print()

        elif args.command == "list-queries":
            queries = papervisor.list_project_queries(args.project_id)
            if not queries:
                msg = f"No search queries found for project '{args.project_id}'."
                print(msg)
                return

            # Show project info if available
            project_info = papervisor.get_project(args.project_id)
            if project_info is not None:
                print(f"Project: {project_info.title}")
                print()

            print(f"Found {len(queries)} search queries:")
            for query in queries:
                print(f"  - {query.id}: {query.topic}")
                print(f"    Query: {query.query}")
                print(f"    Executed: {query.executed_date}")
                print(f"    Extractor: {query.extractor}")
                print(f"    Results file: {query.results_file}")
                print()

        elif args.command == "load-query":
            df = papervisor.load_query_results(args.project_id, args.query_id)
            msg = (
                f"Loaded {len(df)} papers for query '{args.query_id}' "
                f"in project '{args.project_id}'"
            )
            print(msg)

            if args.stats:
                stats = papervisor.get_query_statistics(args.project_id, args.query_id)
                print("\nStatistics:")
                print(f"  Total papers: {stats['total_papers']}")
                if "citation_stats" in stats:
                    cs = stats["citation_stats"]
                    print(f"  Total citations: {cs['total_citations']}")
                    print(f"  Mean citations: {cs['mean_citations']:.1f}")
                if "date_range" in stats:
                    dr = stats["date_range"]
                    print(f"  Year range: {dr['min_year']}-{dr['max_year']}")

        elif args.command == "stats":
            if args.query_id:
                stats = papervisor.get_query_statistics(args.project_id, args.query_id)
                query_info = stats["query_info"]
                print(f"Statistics for query: {query_info['id']}")
                print(f"Project: {query_info.get('project_id', args.project_id)}")
                print(f"Query: {query_info['query_string']}")
                print(f"Topic: {query_info.get('topic', 'N/A')}")
                print(
                    f"Executed: {query_info['executed_date']} via "
                    f"{query_info['extractor']}"
                )
            else:
                stats = papervisor.get_project_statistics(args.project_id)
                project_info = papervisor.get_project(args.project_id)
                if project_info is not None:
                    print(f"Combined statistics for project: {project_info.title}")
                else:
                    print(f"Combined statistics for project: {args.project_id}")

            print("\nDataset Statistics:")
            print(f"  Total papers: {stats['total_papers']}")

            if "citation_stats" in stats:
                cs = stats["citation_stats"]
                print("  Citations:")
                print(f"    Total: {cs['total_citations']}")
                print(f"    Mean: {cs['mean_citations']:.1f}")
                print(f"    Median: {cs['median_citations']:.1f}")
                print(f"    Max: {cs['max_citations']}")

            if "date_range" in stats:
                dr = stats["date_range"]
                print(f"  Year range: {dr['min_year']}-{dr['max_year']}")

            if "top_sources" in stats:
                print("  Top sources:")
                for source, count in list(stats["top_sources"].items())[:5]:
                    print(f"    {source}: {count}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
