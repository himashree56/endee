"""Command-line interface for PDF semantic search."""
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from config import Config
from search_engine import SemanticSearchEngine

console = Console()


@click.group()
def cli():
    """PDF Semantic Search Engine powered by Endee."""
    pass


@cli.command()
@click.option('--pdf-dir', type=click.Path(exists=True), help='Directory containing PDFs')
def ingest(pdf_dir):
    """Ingest PDFs into the search engine."""
    engine = SemanticSearchEngine()
    
    # Initialize collection
    if not engine.initialize():
        console.print("[red]Failed to initialize Endee collection[/red]")
        return
    
    # Ingest PDFs
    pdf_path = Path(pdf_dir) if pdf_dir else Config.PDF_DIR
    
    if not pdf_path.exists():
        console.print(f"[red]Directory not found: {pdf_path}[/red]")
        return
    
    success = engine.ingest_pdfs(pdf_path)
    
    if success:
        console.print("\n[green]✓ Ingestion completed successfully![/green]")
    else:
        console.print("\n[red]✗ Ingestion failed[/red]")


@cli.command()
@click.argument('query')
@click.option('--top-k', default=5, help='Number of results to return')
@click.option('--file', help='Filter by specific filename')
def search(query, top_k, file):
    """Search for relevant document chunks."""
    engine = SemanticSearchEngine()
    
    console.print(f"\n[bold cyan]Searching for:[/bold cyan] {query}\n")
    
    results = engine.search(query, top_k=top_k, filter_by_file=file)
    
    if not results:
        console.print("[yellow]No results found[/yellow]")
        return
    
    # Display results
    for i, result in enumerate(results, 1):
        metadata = result.get('metadata', {})
        score = result.get('score', 0.0)
        
        # Create result panel
        title = f"Result {i} - {metadata.get('file_name', 'Unknown')} (Page {metadata.get('page', '?')})"
        
        content = f"""
**Score:** {score:.4f}

**Text:**
{metadata.get('text', 'No text available')}

**Source:** {metadata.get('file_path', 'Unknown')}
**Page:** {metadata.get('page', '?')}
**Chunk ID:** {metadata.get('chunk_id', '?')}
"""
        
        panel = Panel(
            Markdown(content),
            title=title,
            border_style="cyan" if i == 1 else "blue"
        )
        
        console.print(panel)
        console.print()


@cli.command()
def info():
    """Display information about the current index."""
    engine = SemanticSearchEngine()
    
    index_info = engine.get_index_info()
    
    if not index_info:
        console.print("[yellow]No index found. Run 'ingest' first.[/yellow]")
        return
    
    # Display index information
    console.print("\n[bold cyan]Index Information[/bold cyan]\n")
    
    console.print(f"[bold]Total Chunks:[/bold] {index_info.get('total_chunks', 0)}")
    console.print(f"[bold]Embedding Model:[/bold] {index_info.get('embedding_model', 'Unknown')}")
    console.print(f"[bold]Embedding Dimension:[/bold] {index_info.get('embedding_dimension', 'Unknown')}")
    
    # Files table
    files = index_info.get('files', {})
    
    if files:
        console.print("\n[bold]Indexed Files:[/bold]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("File Name", style="cyan")
        table.add_column("Chunks", justify="right")
        table.add_column("Pages", justify="right")
        
        for filename, file_data in files.items():
            table.add_row(
                filename,
                str(file_data.get('chunks', 0)),
                str(len(file_data.get('pages', [])))
            )
        
        console.print(table)
    
    console.print()


@cli.command()
@click.confirmation_option(prompt='Are you sure you want to reset the index?')
def reset():
    """Reset the search index (delete all data)."""
    engine = SemanticSearchEngine()
    
    if engine.reset_index():
        console.print("[green]✓ Index reset successfully[/green]")
    else:
        console.print("[red]✗ Failed to reset index[/red]")


@cli.command()
def interactive():
    """Start interactive search mode."""
    engine = SemanticSearchEngine()
    
    console.print("\n[bold cyan]PDF Semantic Search - Interactive Mode[/bold cyan]")
    console.print("Type your query or 'quit' to exit\n")
    
    while True:
        try:
            query = console.input("[bold green]Search:[/bold green] ")
            
            if query.lower() in ['quit', 'exit', 'q']:
                console.print("\n[yellow]Goodbye![/yellow]\n")
                break
            
            if not query.strip():
                continue
            
            console.print()
            results = engine.search(query, top_k=3)
            
            if not results:
                console.print("[yellow]No results found[/yellow]\n")
                continue
            
            for i, result in enumerate(results, 1):
                metadata = result.get('metadata', {})
                score = result.get('score', 0.0)
                
                console.print(f"[bold cyan]{i}. {metadata.get('file_name', 'Unknown')} (Page {metadata.get('page', '?')}) - Score: {score:.4f}[/bold cyan]")
                
                text = metadata.get('text', '')
                preview = text[:200] + "..." if len(text) > 200 else text
                console.print(f"   {preview}\n")
            
        except KeyboardInterrupt:
            console.print("\n\n[yellow]Goodbye![/yellow]\n")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]\n")


@cli.command()
@click.argument('question')
def chat(question):
    """Ask a question using RAG (Retrieval-Augmented Generation)."""
    from rag_agent import RAGAgent
    
    console.print(f"\n[bold cyan]Question:[/bold cyan] {question}\n")
    
    try:
        agent = RAGAgent()
        result = agent.ask(question)
        
        # Display answer
        console.print("[bold green]Answer:[/bold green]")
        console.print(result["answer"])
        
        # Display sources
        if result["sources"]:
            console.print("\n[bold yellow]Sources:[/bold yellow]")
            for i, source in enumerate(result["sources"], 1):
                console.print(f"  {i}. {source}")
        
        console.print()
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command(name='interactive-chat')
def interactive_chat():
    """Start interactive RAG chat mode."""
    from rag_agent import RAGAgent
    
    console.print("\n[bold cyan]PDF RAG Chat - Interactive Mode[/bold cyan]")
    console.print("Ask questions about your documents. Type 'quit' to exit\n")
    
    agent = RAGAgent()
    
    while True:
        try:
            question = console.input("[bold green]You:[/bold green] ")
            
            if question.lower() in ['quit', 'exit', 'q']:
                console.print("\n[yellow]Goodbye![/yellow]\n")
                break
            
            if not question.strip():
                continue
            
            console.print()
            result = agent.ask(question)
            
            # Display answer
            console.print("[bold cyan]Assistant:[/bold cyan]")
            console.print(result["answer"])
            
            # Display sources (compact)
            if result["sources"]:
                sources_str = ", ".join(result["sources"][:3])
                if len(result["sources"]) > 3:
                    sources_str += f" (+{len(result["sources"]) - 3} more)"
                console.print(f"\n[dim]Sources: {sources_str}[/dim]")
            
            console.print()
            
        except KeyboardInterrupt:
            console.print("\n\n[yellow]Goodbye![/yellow]\n")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]\n")


@cli.command()
@click.option('--file', help='Specific document to summarize')
@click.option('--length', type=click.Choice(['short', 'medium', 'long']), default='medium', help='Summary length')
@click.option('--all', 'summarize_all', is_flag=True, help='Summarize all documents')
def summarize(file, length, summarize_all):
    """Summarize documents from the vector database."""
    from summarizer import DocumentSummarizer
    
    summarizer = DocumentSummarizer()
    
    if summarize_all:
        # Summarize all documents
        console.print("\n[bold cyan]Summarizing all documents...[/bold cyan]\n")
        summaries = summarizer.summarize_all_documents(max_length=length)
        
        if not summaries:
            console.print("[yellow]No documents found in the database[/yellow]\n")
            return
        
        for i, result in enumerate(summaries, 1):
            console.print(f"[bold green]{i}. {result['filename']}[/bold green]")
            console.print(f"   Chunks: {result['chunk_count']}, Pages: {result['page_count']}")
            console.print(f"\n{result['summary']}\n")
            console.print("-" * 80 + "\n")
    
    elif file:
        # Summarize specific document
        console.print(f"\n[bold cyan]Summarizing: {file}[/bold cyan]\n")
        result = summarizer.summarize_document(file, max_length=length)
        
        if "error" in result:
            console.print(f"[red]{result['summary']}[/red]\n")
            return
        
        console.print(f"[bold]Document:[/bold] {result['filename']}")
        console.print(f"[bold]Chunks:[/bold] {result['chunk_count']}")
        console.print(f"[bold]Pages:[/bold] {result['page_count']}\n")
        console.print("[bold green]Summary:[/bold green]")
        console.print(result['summary'])
        console.print()
    
    else:
        console.print("[yellow]Please specify --file or --all[/yellow]")
        console.print("Example: python cli.py summarize --file document.pdf")
        console.print("         python cli.py summarize --all --length short")


@cli.command(name='list-documents')
def list_documents():
    """List all documents available in the vector database."""
    from summarizer import DocumentSummarizer
    
    summarizer = DocumentSummarizer()
    documents = summarizer.get_available_documents()
    
    if not documents:
        console.print("\n[yellow]No documents found in the database[/yellow]\n")
        return
    
    console.print("\n[bold cyan]Available Documents:[/bold cyan]\n")
    
    # Get index info for details
    index_info = summarizer.search_engine.get_index_info()
    files = index_info.get("files", {})
    
    for i, doc in enumerate(documents, 1):
        file_info = files.get(doc, {})
        chunks = file_info.get("chunks", 0)
        pages = len(file_info.get("pages", []))
        
        console.print(f"{i}. [bold]{doc}[/bold]")
        console.print(f"   Chunks: {chunks}, Pages: {pages}")
    
    console.print()


@cli.command(name='adaptive-rag')
@click.argument('question')
def adaptive_rag(question):
    """Ask a question using Adaptive Reasoning RAG with explainability."""
    from adaptive_rag_agent import AdaptiveRAGAgent
    import json
    
    console.print(f"\n[bold cyan]Question:[/bold cyan] {question}\n")
    console.print("[dim]Running adaptive reasoning...[/dim]\n")
    
    try:
        agent = AdaptiveRAGAgent()
        result = agent.ask(question)
        
        # Display query analysis
        console.print("[bold yellow]📊 Query Analysis:[/bold yellow]")
        analysis = result["query_analysis"]
        console.print(f"  Complexity: {analysis.get('complexity', 'N/A')}")
        console.print(f"  Type: {analysis.get('query_type', 'N/A')}")
        console.print()
        
        # Display reasoning steps
        console.print("[bold yellow]🧠 Reasoning Steps:[/bold yellow]")
        for step in result["reasoning_steps"]:
            console.print(f"  • {step['step']}: {step['details']}")
        console.print()
        
        # Display answer
        console.print("[bold green]💡 Answer:[/bold green]")
        console.print(result["answer"])
        console.print()
        
        # Display confidence
        confidence = result["confidence"]
        confidence_color = "green" if confidence > 0.7 else "yellow" if confidence > 0.4 else "red"
        console.print(f"[bold {confidence_color}]🎯 Confidence: {confidence:.1%}[/bold {confidence_color}]")
        console.print()
        
        # Display sources
        if result["sources"]:
            console.print("[bold yellow]📚 Sources:[/bold yellow]")
            for i, source in enumerate(result["sources"], 1):
                console.print(f"  {i}. {source}")
        console.print()
        
        # Display retrieval iterations
        if len(result["retrieval_iterations"]) > 1:
            console.print("[bold yellow]🔄 Retrieval Iterations:[/bold yellow]")
            for iteration in result["retrieval_iterations"]:
                console.print(f"  Iteration {iteration['iteration']}: {iteration['num_results']} docs (avg score: {iteration['avg_score']:.3f})")
            console.print()
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    cli()
