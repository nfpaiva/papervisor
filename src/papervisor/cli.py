"""Command line interface for papervisor."""

import argparse
import sys
from typing import Dict, Any

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

    # PDF management commands
    pdf_parser = subparsers.add_parser("pdf", help="PDF management commands")
    pdf_subparsers = pdf_parser.add_subparsers(dest="pdf_command", help="PDF commands")

    # List PDFs command
    list_pdfs_parser = pdf_subparsers.add_parser("list", help="List downloaded PDFs")
    list_pdfs_parser.add_argument("project_id", help="Project ID")
    list_pdfs_parser.add_argument("--query-id", help="Query ID (optional)")
    list_pdfs_parser.add_argument(
        "--data-dir", default="data", help="Data directory path"
    )

    # PDF stats command
    pdf_stats_parser = pdf_subparsers.add_parser(
        "stats", help="Show PDF download statistics"
    )
    pdf_stats_parser.add_argument("project_id", help="Project ID")
    pdf_stats_parser.add_argument(
        "--data-dir", default="data", help="Data directory path"
    )

    # PDF directory command
    pdf_dir_parser = pdf_subparsers.add_parser("dir", help="Show PDF directory path")
    pdf_dir_parser.add_argument("project_id", help="Project ID")
    pdf_dir_parser.add_argument("--query-id", help="Query ID (optional)")
    pdf_dir_parser.add_argument(
        "--data-dir", default="data", help="Data directory path"
    )

    # Download PDFs command
    download_parser = pdf_subparsers.add_parser(
        "download", help="Download PDFs automatically"
    )
    download_parser.add_argument("project_id", help="Project ID")
    download_parser.add_argument(
        "--query-id", help="Query ID (if not provided, downloads all queries)"
    )
    download_parser.add_argument(
        "--max-downloads",
        type=int,
        help="Maximum number of PDFs to download (for testing)",
    )
    download_parser.add_argument(
        "--data-dir", default="data", help="Data directory path"
    )

    # Download status command
    status_parser = pdf_subparsers.add_parser(
        "status", help="Show download status and reports"
    )
    status_parser.add_argument("project_id", help="Project ID")
    status_parser.add_argument("--query-id", help="Query ID (optional)")
    status_parser.add_argument("--data-dir", default="data", help="Data directory path")

    # List manual downloads command
    manual_parser = pdf_subparsers.add_parser(
        "manual", help="List papers requiring manual download"
    )
    manual_parser.add_argument("project_id", help="Project ID")
    manual_parser.add_argument("--query-id", help="Query ID (optional)")
    manual_parser.add_argument("--data-dir", default="data", help="Data directory path")

    # Web server command
    web_parser = pdf_subparsers.add_parser(
        "web", help="Start web interface for PDF management"
    )
    web_parser.add_argument("project_id", help="Project ID")
    web_parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    web_parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    web_parser.add_argument("--data-dir", default="data", help="Data directory path")

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

        elif args.command == "pdf":
            if not args.pdf_command:
                pdf_parser.print_help()
                return

            if args.pdf_command == "list":
                pdfs = papervisor.list_downloaded_pdfs(args.project_id, args.query_id)
                if not pdfs:
                    location = (
                        f"query '{args.query_id}'" if args.query_id else "project"
                    )
                    print(f"No PDFs found for {location} '{args.project_id}'.")
                    return

                location = f"query '{args.query_id}'" if args.query_id else "project"
                print(f"Found {len(pdfs)} PDFs for {location} '{args.project_id}':")
                for pdf_path in sorted(pdfs):
                    print(f"  - {pdf_path.name}")

            elif args.pdf_command == "stats":
                stats = papervisor.get_pdf_download_stats(args.project_id)
                project_info = papervisor.get_project(args.project_id)

                if project_info is not None:
                    print(f"PDF download statistics for: {project_info.title}")
                else:
                    print(f"PDF download statistics for project: {args.project_id}")

                print(f"\nTotal PDFs: {stats.get('total', 0)}")
                print("\nPer query:")
                for query_id, count in sorted(stats.items()):
                    if query_id != "total":
                        print(f"  {query_id}: {count} PDFs")

            elif args.pdf_command == "dir":
                pdf_dir = papervisor.get_pdf_directory(args.project_id, args.query_id)
                location = f"query '{args.query_id}'" if args.query_id else "project"
                print(f"PDF directory for {location} '{args.project_id}':")
                print(f"  {pdf_dir}")
                if not pdf_dir.exists():
                    print("  (Directory will be created when needed)")

            elif args.pdf_command == "download":
                # Always download all queries for a project
                print(
                    f"Starting PDF download for all queries in project "
                    f"'{args.project_id}'..."
                )

                # Ignore query_id parameter since we always download everything
                if args.query_id:
                    print(
                        "Note: --query-id is ignored. Downloading all queries "
                        "for project consistency."
                    )

                results = papervisor.download_project_pdfs(
                    args.project_id, max_downloads=args.max_downloads
                )

                # Calculate totals across all queries
                total_success = 0
                total_existed = 0
                total_failed = 0
                total_manual = 0
                total_processed = 0

                print("Per Query Results:")
                for query_id, query_results in results.items():
                    success = sum(1 for r in query_results if r.status == "success")
                    existed = sum(
                        1 for r in query_results if r.status == "already_existed"
                    )
                    failed = sum(1 for r in query_results if r.status == "failed")
                    manual = sum(
                        1 for r in query_results if r.status == "manual_required"
                    )

                    total_success += success
                    total_existed += existed
                    total_failed += failed
                    total_manual += manual
                    total_processed += len(query_results)

                    print(
                        f"  {query_id}: {success} downloaded, {existed} existed, "
                        f"{manual} manual, {failed} failed"
                    )

                print("Overall Project Download Summary:")
                print(f"  Successfully downloaded: {total_success}")
                print(f"  Already existed: {total_existed}")
                print(f"  Manual required: {total_manual}")
                print(f"  Failed: {total_failed}")
                print(f"  Total processed: {total_processed}")

            elif args.pdf_command == "status":
                download_stats: Dict[str, Any] = papervisor.get_download_statistics(
                    args.project_id, args.query_id
                )

                if args.query_id:
                    print(
                        f"Download status for query '{args.query_id}' in project "
                        f"'{args.project_id}':"
                    )
                else:
                    print(f"Download status for project '{args.project_id}':")

                if "by_query" in download_stats:
                    # Project-wide stats
                    summary = download_stats.get("summary", download_stats)
                    print("Overall Statistics:")
                    print(f"  Total papers: {summary.get('total_papers', 0)}")
                    print(
                        f"  Successfully downloaded: "
                        f"{summary.get('successful_downloads', 0)}"
                    )
                    print(f"  Failed downloads: {summary.get('failed_downloads', 0)}")
                    print(
                        f"  Manual downloads required: "
                        f"{summary.get('manual_required', 0)}"
                    )
                    print(f"  Already existed: {summary.get('already_existed', 0)}")

                    print("Per Query:")
                    for query_id, query_stats in download_stats["by_query"].items():
                        print(f"  {query_id}:")
                        print(f"    Total: {query_stats.get('total_papers', 0)}")
                        print(
                            f"    Downloaded: "
                            f"{query_stats.get('successful_downloads', 0)}"
                        )
                        print(f"    Failed: {query_stats.get('failed_downloads', 0)}")
                        print(
                            f"    Manual required: "
                            f"{query_stats.get('manual_required', 0)}"
                        )
                        print(
                            f"    Already existed: "
                            f"{query_stats.get('already_existed', 0)}"
                        )
                else:
                    # Single query stats
                    print(f"  Total papers: {download_stats.get('total_papers', 0)}")
                    print(
                        f"  Successfully downloaded: "
                        f"{download_stats.get('successful_downloads', 0)}"
                    )
                    print(
                        f"  Failed downloads: "
                        f"{download_stats.get('failed_downloads', 0)}"
                    )
                    print(
                        f"  Manual downloads required: "
                        f"{download_stats.get('manual_required', 0)}"
                    )
                    print(
                        f"  Already existed: "
                        f"{download_stats.get('already_existed', 0)}"
                    )

            elif args.pdf_command == "manual":
                # List papers requiring manual download
                manual_papers = papervisor.list_manual_download_candidates(
                    args.project_id, args.query_id
                )

                if manual_papers.empty:
                    location = (
                        f"query '{args.query_id}'" if args.query_id else "project"
                    )
                    print(
                        f"No papers requiring manual download found for "
                        f"{location} '{args.project_id}'."
                    )
                else:
                    location = (
                        f"query '{args.query_id}'" if args.query_id else "project"
                    )
                    print(
                        f"Papers requiring manual download for {location} "
                        f"'{args.project_id}':"
                    )

                    for idx, paper in manual_papers.iterrows():
                        print(f"\nPaper ID: {paper.get('paper_id', idx)}")
                        print(f"Title: {paper.get('title', 'N/A')}")
                        print(f"Status: {paper.get('status', 'N/A')}")
                        if "error_message" in paper and paper["error_message"]:
                            print(f"Error: {paper['error_message']}")

                # Show directory for manual downloads
                manual_dir = papervisor.get_pdf_directory(
                    args.project_id, args.query_id
                )
                manual_dir = manual_dir.parent / "manual" / (args.query_id or "")
                print(f"\nManual download directory: {manual_dir}")
                if not manual_dir.exists():
                    print("  (Directory will be created when needed)")

            elif args.pdf_command == "web":
                # Start web interface
                from .web_server import PapervisorWebServer

                print(f"Starting web interface for project '{args.project_id}'...")
                print(f"Access the dashboard at: http://{args.host}:{args.port}")
                print("Press Ctrl+C to stop the server")

                server = PapervisorWebServer(args.project_id, args.data_dir)
                server.run(host=args.host, port=args.port, debug=False)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
