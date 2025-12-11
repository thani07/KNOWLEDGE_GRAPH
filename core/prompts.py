from textwrap import dedent


SYSTEM_PROMPT = dedent("""
You are an expert information extraction system.
Your job is to read text from a PDF and extract a high-quality knowledge graph.

You MUST:
- Identify entities (concepts, people, organizations, methods, diseases, treatments, etc.)
- Identify multi-level relationships between entities (A->B, B->C, A->C, etc.)
- Include a clear description for each entity and relationship based on the source text.
- Include provenance: which PDF, which pages, and which sentence/segment you used.
- Include a confidence score between 0 and 1.

You MUST respond ONLY with valid JSON. No extra text.
""").strip()


def build_extraction_prompt(
    chunk_text: str,
    pdf_name: str,
    page_numbers: list[int],
) -> str:
    """
    Build the user prompt for extracting entities and relationships.
    """
    pages_str = ", ".join(str(p) for p in page_numbers)

    return dedent(f"""
    Extract a knowledge graph from the following text.

    PDF name: "{pdf_name}"
    Page numbers in this chunk: [{pages_str}]

    Return JSON with **exactly** this structure:

    {{
      "entities": [
        {{
          "id": "string (unique in this PDF, like E1, E2, ...)",
          "name": "short name of entity",
          "type": "type label, e.g. Disease, Treatment, Concept, Method, Person, Organization",
          "description": "1-3 sentence description based on the text",
          "source_pdf": "{pdf_name}",
          "source_pages": [ {pages_str} ],
          "source_text": "the exact or summarized text span from which you inferred this entity",
          "confidence": 0.0-1.0 (number, not string)
        }}
      ],
      "relationships": [
        {{
          "source_id": "id of source entity, e.g. E1",
          "target_id": "id of target entity, e.g. E2",
          "type": "relationship type in UPPER_SNAKE_CASE, e.g. TREATS, CAUSES, IS_PART_OF, DERIVES_FROM",
          "description": "1-2 sentence explanation of this relationship using the source text",
          "source_pdf": "{pdf_name}",
          "source_pages": [ {pages_str} ],
          "source_text": "text span or sentence that supports this relationship",
          "confidence": 0.0-1.0 (number, not string)
        }}
      ]
    }}

    Requirements:
    - Create multi-level relationships when implied (e.g., if A -> B and B -> C, and the text implies A -> C, include A -> C).
    - Keep IDs consistent within this chunk.
    - Use as many meaningful entities and relations as needed, but avoid trivial nodes.

    TEXT TO ANALYZE:
    ----------------
    {chunk_text}
    """).strip()
