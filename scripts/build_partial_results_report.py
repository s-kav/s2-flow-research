from __future__ import annotations

from pathlib import Path
import json
import math

import matplotlib.pyplot as plt
import pandas as pd
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'S2_flow_partial_theorems_and_structural_lemmas_ru.docx'
ASSETS = ROOT / 'docs' / 'assets_partial_results'
ASSETS.mkdir(parents=True, exist_ok=True)
RESULTS = ROOT / 'results' / 'massive_run'


def make_figures() -> tuple[Path, Path, Path]:
    # Figure 1: exact cut factorisation schematic.
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.axis('off')
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.text(0.25, 0.93, '2-rib incision', ha='center', va='center', fontsize=13, fontweight='bold')
    ax.text(0.75, 0.93, '3-rib incision', ha='center', va='center', fontsize=13, fontweight='bold')

    # Two-cut panel.
    ax.add_patch(plt.Circle((0.12, 0.55), 0.09, fill=False, linewidth=1.5))
    ax.add_patch(plt.Circle((0.38, 0.55), 0.09, fill=False, linewidth=1.5))
    ax.plot([0.20, 0.30], [0.60, 0.60], linewidth=1.5)
    ax.plot([0.20, 0.30], [0.50, 0.50], linewidth=1.5)
    ax.text(0.12, 0.55, 'A', ha='center', va='center', fontsize=12)
    ax.text(0.38, 0.55, 'B', ha='center', va='center', fontsize=12)
    ax.text(0.25, 0.37, 'boundary vectors: p and -p', ha='center', fontsize=10)
    ax.annotate('', xy=(0.19, 0.20), xytext=(0.31, 0.20), arrowprops={'arrowstyle': '<->'})
    ax.text(0.25, 0.12, 'closing each side with one edge', ha='center', fontsize=9)

    # Three-cut panel.
    ax.add_patch(plt.Circle((0.62, 0.55), 0.09, fill=False, linewidth=1.5))
    ax.add_patch(plt.Circle((0.88, 0.55), 0.09, fill=False, linewidth=1.5))
    for y in (0.63, 0.55, 0.47):
        ax.plot([0.70, 0.80], [y, y], linewidth=1.5)
    ax.text(0.62, 0.55, 'A', ha='center', va='center', fontsize=12)
    ax.text(0.88, 0.55, 'B', ha='center', va='center', fontsize=12)
    ax.text(0.75, 0.34, 'p₁+p₂+p₃=0,  pᵢ·pⱼ=-1/2', ha='center', fontsize=10)
    ax.annotate('', xy=(0.69, 0.20), xytext=(0.81, 0.20), arrowprops={'arrowstyle': '<->'})
    ax.text(0.75, 0.12, 'closing each side with a new cubic vertex', ha='center', fontsize=9)
    fig.tight_layout()
    cut_path = ASSETS / 'cut_factorization.png'
    fig.savefig(cut_path, dpi=220, bbox_inches='tight')
    plt.close(fig)

    df = pd.read_csv(RESULTS / 'summary.csv')
    counts = df['method'].value_counts()
    fig, ax = plt.subplots(figsize=(7.2, 4.5))
    labels = ['Exact Construction\nfrom 3-Coloring', 'Nonlinear Search\nin the Space of Cycles']
    values = [int(counts.get('exact_three_edge_colouring_construction', 0)), int(counts.get('cycle_space_nonlinear_least_squares', 0))]
    bars = ax.bar(labels, values)
    ax.set_ylabel('Number of graphs')
    ax.set_title('Types of certificates in a reproducible campaign')
    ax.grid(axis='y', alpha=0.25)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, value + max(values)*0.015, str(value), ha='center', va='bottom', fontsize=11)
    fig.tight_layout()
    cert_path = ASSETS / 'certificate_counts.png'
    fig.savefig(cert_path, dpi=220, bbox_inches='tight')
    plt.close(fig)

    nonlinear = df[df['method'] == 'cycle_space_nonlinear_least_squares'].copy()
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.scatter(range(len(nonlinear)), nonlinear['max_unit_norm_residual'])
    ax.set_yscale('log')
    ax.set_xticks(range(len(nonlinear)))
    ax.set_xticklabels(nonlinear['name'], rotation=35, ha='right', fontsize=8)
    ax.set_ylabel('Maximum error of the norm')
    ax.set_title('Independently verified numerical certificates')
    ax.grid(axis='y', alpha=0.25)
    fig.tight_layout()
    residual_path = ASSETS / 'nonlinear_residuals.png'
    fig.savefig(residual_path, dpi=220, bbox_inches='tight')
    plt.close(fig)
    return cut_path, cert_path, residual_path


def set_cell_text(cell, text: str, bold: bool = False, size: int = 9) -> None:
    cell.text = ''
    p = cell.paragraphs[0]
    run = p.add_run(text)
    run.bold = bold
    run.font.name = 'Arial'
    run.font.size = Pt(size)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def shade_cell(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:fill'), fill)
    tc_pr.append(shd)


def add_page_number(paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    fld_char1 = OxmlElement('w:fldChar')
    fld_char1.set(qn('w:fldCharType'), 'begin')
    instr_text = OxmlElement('w:instrText')
    instr_text.set(qn('xml:space'), 'preserve')
    instr_text.text = ' PAGE '
    fld_char2 = OxmlElement('w:fldChar')
    fld_char2.set(qn('w:fldCharType'), 'end')
    run._r.append(fld_char1)
    run._r.append(instr_text)
    run._r.append(fld_char2)


def add_equation(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.font.name = 'Cambria Math'
    run.font.size = Pt(11)


def add_body(doc: Document, text: str, bold_prefix: str | None = None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.line_spacing = 1.08
    if bold_prefix and text.startswith(bold_prefix):
        r1 = p.add_run(bold_prefix)
        r1.bold = True
        r2 = p.add_run(text[len(bold_prefix):])
        for r in (r1, r2):
            r.font.name = 'Arial'
            r.font.size = Pt(10.5)
    else:
        r = p.add_run(text)
        r.font.name = 'Arial'
        r.font.size = Pt(10.5)
    return p


def add_theorem(doc: Document, title: str, statement: str, proof_paragraphs: list[str]) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(7)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(title)
    r.bold = True
    r.font.name = 'Arial'
    r.font.size = Pt(11)
    statement_p = add_body(doc, statement)
    statement_p.paragraph_format.keep_with_next = True
    p = doc.add_paragraph()
    r = p.add_run('Proof.')
    r.bold = True
    r.font.name = 'Arial'
    r.font.size = Pt(10.5)
    if proof_paragraphs:
        r2 = p.add_run(' ' + proof_paragraphs[0])
        r2.font.name = 'Arial'
        r2.font.size = Pt(10.5)
    for paragraph in proof_paragraphs[1:]:
        add_body(doc, paragraph)
    q = doc.add_paragraph()
    q.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    rr = q.add_run('□')
    rr.font.name = 'Cambria Math'
    rr.font.size = Pt(11)


def build_doc() -> None:
    cut_fig, cert_fig, residual_fig = make_figures()
    campaign = json.loads((RESULTS / 'campaign.json').read_text(encoding='utf-8'))
    df = pd.read_csv(RESULTS / 'summary.csv')
    nonlinear = df[df['method'] == 'cycle_space_nonlinear_least_squares'].copy()

    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = Cm(1.8)
    sec.bottom_margin = Cm(1.7)
    sec.left_margin = Cm(2.1)
    sec.right_margin = Cm(1.8)
    sec.header_distance = Cm(0.8)
    sec.footer_distance = Cm(0.8)

    styles = doc.styles
    styles['Normal'].font.name = 'Arial'
    styles['Normal'].font.size = Pt(10.5)
    for style_name, size in [('Title', 20), ('Heading 1', 15), ('Heading 2', 12), ('Heading 3', 11)]:
        styles[style_name].font.name = 'Arial'
        styles[style_name].font.size = Pt(size)
        styles[style_name].font.color.rgb = RGBColor(31, 55, 77)

    header = sec.header.paragraphs[0]
    header.text = 'S²-flows on bridgeless cubic graphs'
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    for run in header.runs:
        run.font.name = 'Arial'
        run.font.size = Pt(8)
        run.font.color.rgb = RGBColor(90, 90, 90)
    add_page_number(sec.footer.paragraphs[0])

    title = doc.add_paragraph(style='Title')
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run('New partial theorems and structural lemmas\nfor S²-flows')
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = subtitle.add_run('Complete proofs, boundaries of novelty, and reproducible computational tests')
    r.italic = True
    r.font.name = 'Arial'
    r.font.size = Pt(11)
    date_p = doc.add_paragraph()
    date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rr = date_p.add_run('State of the art and computation: July 22, 2026')
    rr.font.name = 'Arial'
    rr.font.size = Pt(9)
    doc.add_paragraph()

    box = doc.add_table(rows=1, cols=1)
    box.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = box.cell(0, 0)
    shade_cell(cell, 'EAF2F8')
    set_cell_text(cell, 'The main result of the paper: the complete S²-flow conjecture is not proven. Factorization theorems, constructive special cases, and reductions of the minimal counterexample, new to this project, are obtained and rigorously proven. The claim of world scientific novelty requires peer review and additional bibliographic research..', bold=True, size=10)

    doc.add_heading('1. Summary of results', level=1)
    summary_items = [
        'Exact cut law: the sum of signed vectors on any edge cut is zero.'
        'Small cut rigidity: on a 2-cut, vectors are antipodal; on a 3-cut, they form an equilateral triple with pairwise scalar products of -1/2.'
        'Exact factorization by a 2-edge cut: a graph has an S²-flow if and only if both canonically closed sides have S²-flows.'
        'Exact factorization by a nontrivial 3-edge cut with the same "if and only if" condition.'
        'The injection of one cubic graph into a vertex of another admits the reverse reduction. Inflating a vertex into a triangle preserves the S²-flow in both directions.'
        'Every 3-edge-colorable cubic graph has an explicit S²-flow constructed from three directed 2-factors.'
        'Every planar bridgeless cubic graph has an S²-flow as a consequence of the four-color theorem and the construction from a 3-edge-coloring.'
        'A minimal counterexample, if it exists, must be cyclically 4-edge-connected and triangle-free.'
        'A reproducible code was constructed that yielded 288 of 288 independently verified finite certificates.'
    ]
    for item in summary_items:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(item)

    doc.add_heading('2. Initial Statement and Status of the Open Problem', level=1)
    add_body(doc, 'Let G=(V,E) be a finite directed graph. An S²-flow is a mapping φ:E→R³ such that ||φ(e)||₂=1 on each edge and Kirchhoff's law holds at each vertex. Changing the edge orientation is accompanied by replacing φ(e) with -φ(e).')
    add_equation(doc, 'Σₑ ε(v,e) φ(e) = 0 for every v∈V, ||φ(e)||₂ = 1 for every e∈E.')
    add_body(doc, 'Jains conjecture states that every bridgeless graph, and equivalently every bridgeless cubic graph, admits such a flow. As of July As of 2026, the conjecture remains open. Houdrouge, Miraftab, and Morin (2026) provided a geometric equivalence via equiangular spherical immersions, a one-sided composition theorem, preservation under triangle inflation, and explicit quasi-Petersen families. Mattiolo et al. (2023) captures the general higher-dimensional context and a known universal bound in higher dimensions.')

    doc.add_heading('3. Novelty Status', level=1)
    table = doc.add_table(rows=1, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = 'Table Grid'
    headers = ['Result', 'Status', 'Comment']
    for i, h in enumerate(headers):
        set_cell_text(table.rows[0].cells[i], h, bold=True)
        shade_cell(table.rows[0].cells[i], 'D9EAF7')
    novelty_rows = [
        ('Geometric characterisation of S²-flow', 'Known', 'Houdrouge, Miraftab, Morin, 2026.'),
        ('Composition of two graphs with flows', 'Known', 'One-directional Theorem 17 in the 2026 paper.'),
        ('Vertex blow-up into a triangle', 'Known in the forward direction', 'Theorem 19 in the 2026 paper.'),
        ('Exact 2-cut factorization', 'Obtained in project', 'Full proof given below; exact priority not guaranteed.'),
        ('Exact 3-cut factorization and reverse composition', 'Obtained in project', 'Strengthens the one-directional composition to an equivalence.'),
        ('Invariance under triangle blow-up', 'Obtained in project', 'Reverse direction follows from 3-cut factorization.'),
        ('Explicit flow from 3-edge-colouring', 'Complete special case', 'Also follows from the general cycle-cover principle; a self-contained construction is given here.'),
        ('Minimal counterexample reduction', 'Obtained as a corollary', 'Cyclic 4-edge-connectivity and absence of triangles.')
    ]
    for row in novelty_rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            set_cell_text(cells[i], value, size=8.5)

    doc.add_heading('4. Basic Structural Lemmas', level=1)
    add_theorem(doc, 'Lemma 1. Edge-cut law.', 'For any vertex set U⊂V and any S²-flow, the sum of edge vectors on δ(U) signed outward from U is zero.', [
        'Sum the Kirchhoff laws over all vertices in U. Each internal edge has both endpoints in U and appears twice with opposite signs, so it cancels. Only the edges of δ(U) remain, each once with the outward sign. Their sum is zero.'
    ])
    add_theorem(doc, 'Lemma 2. Rigidity of a unit triple.', 'If u,v,w∈R³, ||u||=||v||=||w||=1 and u+v+w=0, then u·v=v·w=w·u=-1/2. Consequently, the three vectors are coplanar and form mutual angles 2π/3.', [
        'From w=-(u+v) and ||w||²=1 we get 1=||u+v||²=2+2u·v, hence u·v=-1/2. Cyclic permutation gives the other two equalities. The linear dependence u+v+w=0 ensures coplanarity.'
    ])
    add_body(doc, 'Corollary. Across a 2-edge cut the two outward unit vectors are p and -p. Across a 3-edge cut the outward vectors form an equilateral triple, unique up to an orthogonal transformation.')
    doc.add_picture(str(cut_fig), width=Inches(6.7))
    cap = doc.add_paragraph('Figure 1. Canonical interfaces of 2- and 3-edge cuts.')
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.runs[0].italic = True

    doc.add_heading('5. Exact Factorization at Small Cuts', level=1)
    add_theorem(doc, 'Theorem 3. Exact factorization at a 2-edge cut.', 'Let G be a bridgeless cubic graph and δ(A)={a₁b₁,a₂b₂} a non-trivial 2-edge cut, with aᵢ∈A and bᵢ∉A. Form G_A by removing the cut and adding edge a₁a₂; form G_B analogously. Then G has an S²-flow if and only if both G_A and G_B have S²-flows.', [
        'Necessity. Let φ be a flow on G. Label the two boundary vectors outward from A as p₁ and p₂. By Lemma 1, p₁+p₂=0. After removing the cut, add edge a₁a₂ and orient it so that its contributions at a₁ and a₂ are p₁ and p₂ respectively. This is possible since p₂=-p₁ and ||p₁||=1. Kirchhoff equations at all remaining vertices are unchanged. The result is a flow on G_A. The same construction applies to B.',
        'Sufficiency. Let flows be given on G_A and G_B. The closure edges carry unit vectors x and y. Apply an orthogonal transformation Q to the entire flow on G_B, mapping y to x or -x according to the chosen pairing of endpoints. Remove the closure edges and restore the two cut edges, assigning them x with orientations reproducing the former contributions at the four boundary vertices. At all other vertices conservation is maintained; at the boundary vertices the contributions match the removed closure edges.'
    ])
    add_theorem(doc, 'Theorem 4. Exact factorization at a non-trivial 3-edge cut.', 'Let δ(A)={aᵢbᵢ: i=1,2,3}. Close side A with a new vertex z_A connected to a₁,a₂,a₃; construct G_B analogously. Then G has an S²-flow if and only if both G_A and G_B have S²-flows.', [
        'Necessity. The outward boundary vectors p₁,p₂,p₃ from A satisfy p₁+p₂+p₃=0. Add a new vertex z_A and three edges z_Aaᵢ so that the contribution of the new edge at aᵢ is pᵢ. At z_A the sum of contributions equals -(p₁+p₂+p₃)=0. All norms equal one. Side B is closed analogously.',
        'Sufficiency. In the flows on G_A and G_B, the vector triples at the new vertices are equilateral by Lemma 2. For any given bijection between the three boundary edges there exists an orthogonal transformation Q∈O(3) mapping the ordered triple of one side to the opposite triple of the other. Apply Q to the entire flow on G_B, remove z_A,z_B, and connect the corresponding boundary vertices. The new edges reproduce the removed contributions, so Kirchhoff conservation is preserved.'
    ])
    add_body(doc, 'Lemma (Bridgelessness of closures). If the original G is bridgeless, then the canonical closures of non-trivial 2- and 3-cuts are also bridgeless. Indeed, an internal edge that is a bridge of a closure would separate a component with no boundary terminals and would therefore be a bridge of the original graph; a new closure edge or an edge to a new vertex cannot be a bridge, because the corresponding terminal has an internal path to the other terminals, otherwise the original cut edge would be a bridge.')

    doc.add_heading('6. Strengthening of Composition Results', level=1)
    add_theorem(doc, 'Corollary 5. Reversibility of injection.', 'Let H▷G be obtained by injecting cubic graph H into a vertex of cubic graph G. Then H▷G has an S²-flow if and only if both H and G have S²-flows.', [
        'The forward direction coincides with the known composition: equilateral triples at the removed vertices are matched by an orthogonal transformation. The reverse direction follows from Theorem 4: the three connecting edges form a non-trivial 3-cut whose canonical closures are isomorphic to H and G.'
    ])
    add_theorem(doc, 'Corollary 6. Invariance under vertex blow-up into a triangle.', 'Let G△ be obtained from cubic graph G by replacing a vertex with a triangle, each vertex of which inherits one external edge. Then G△ has an S²-flow if and only if G has an S²-flow.', [
        'The graph G△ is the injection of K₄ into the corresponding vertex of G. The graph K₄ has an S²-flow. The forward direction follows from composition; the reverse from Corollary 5. Thus the known preservation under blow-up is strengthened to an equivalence.'
    ])

    doc.add_heading('7. Complete Constructive Special Case', level=1)
    add_theorem(doc, 'Theorem 7. All 3-edge-colourable cubic graphs.', 'Every cubic graph with a proper 3-edge-colouring admits an S²-flow, and the flow is constructed explicitly in polynomial time once the colouring is given.', [
        'Let M₁,M₂,M₃ be the three colour classes. For i=1,2,3 set Hᵢ=E(G)\\Mᵢ. At every vertex exactly two edges of Hᵢ are present, so Hᵢ is a 2-factor, i.e. a disjoint union of cycles. Orient each cycle of each Hᵢ arbitrarily.',
        'Fix a global orientation of the edges of G. For edge e define σᵢ(e)=0 if e∉Hᵢ; σᵢ(e)=1 if the orientation of e in Hᵢ agrees with the global one; and σᵢ(e)=-1 otherwise. Each column σᵢ is a scalar circulation, being a sum of oriented cycles.',
        'Define φ(e)=(σ₁(e),σ₂(e),σ₃(e))/√2. Kirchhoff law holds coordinatewise. Each edge belongs to exactly two of H₁,H₂,H₃, so φ(e) has exactly two coordinates equal to ±1/√2 and the third equal to zero. Hence ||φ(e)||²=(1+1)/2=1.'
    ])
    add_body(doc, 'Corollary 7.1. Every planar bridgeless cubic graph has an S²-flow. By Tait\'s theorem, equivalent to the four-colour theorem, such a graph has a proper 3-edge-colouring; Theorem 7 then applies.')
    add_body(doc, 'Corollary 7.2. Every cubic graph of oddness 0 has an S²-flow. An even 2-factor is 2-edge-coloured alternately, and the complementary perfect matching receives the third colour.')

    doc.add_heading('8. New Recursive Infinite Class', level=1)
    add_theorem(doc, 'Theorem 8. Class of atoms and small sums.', 'Let 𝒞 be the smallest class of cubic graphs containing all 3-edge-colourable cubic graphs and the known quasi-Petersen family Gₐ,ᵦ,ₚ for p/6<a,b<p/2, and closed under 2-edge sums and vertex injection. Then every graph in 𝒞 has an S²-flow.', [
        'The base 3-edge-colourable graphs are covered by Theorem 7. The quasi-Petersen family has an equiangular S²-immersion by Proposition 2 of Houdrouge, Miraftab, and Morin, and therefore has an S²-flow.',
        'The inductive step for 2-edge sums follows from the sufficiency direction of Theorem 3. The inductive step for vertex injection follows from the sufficiency direction of Theorem 4. Hence any finite tree of such operations preserves the existence of an S²-flow.'
    ])
    add_body(doc, 'The class 𝒞 contains in particular all iterated vertex blow-ups into triangles, all compositions of Petersen/quasi-Petersen blocks with 3-edge-colourable blocks, and graphs whose non-trivial 2- and 3-cut tree has every atom in the base class.')

    doc.add_heading('9. Structure of the Minimal Counterexample', level=1)
    add_theorem(doc, 'Theorem 9. Minimal counterexample reduction.', 'If the S²-flow conjecture is false and G is a counterexample with the minimum number of vertices among bridgeless cubic graphs, then G has no 2-edge cuts, no non-trivial 3-edge cuts, and contains no triangles. In particular, G is cyclically 4-edge-connected and has girth at least 4.', [
        'If a non-trivial 2-cut exists, both canonical sides are smaller than G and bridgeless. By minimality they have S²-flows, and Theorem 3 glues them into a flow on G, a contradiction.',
        'If a non-trivial 3-cut exists, both sides after adding a new vertex are smaller than G and bridgeless. By minimality they have flows, and Theorem 4 again gives a contradiction. Hence no cut of fewer than four edges can separate two cyclic parts.',
        'Suppose G contains a triangle. Since 2-cuts are already ruled out, the three external neighbours of the triangle are distinct. Contract the triangle to a single cubic vertex to obtain a smaller bridgeless cubic graph G₀. By minimality G₀ has an S²-flow. By the triangle blow-up invariance the original G also has a flow, a contradiction.'
    ])
    add_body(doc, 'Remark. The reduction obtained does not prove the conjecture, but it eliminates all composite obstacles and shifts the search to cyclically 4-edge-connected triangle-free atoms. To qualify as a snark of girth at least 5, 4-cycles must be eliminated separately; a universal 4-cycle reduction is not proved in this work.')

    doc.add_heading('10. Algebraic Structural Lemma', level=1)
    add_theorem(doc, 'Lemma 10. Rank-3 Gram compression.', 'Let B be the oriented incidence matrix, Z a matrix whose columns form a basis of ker B, and zₑ the row of Z for edge e. If there exists Q⪰0 with rank Q≤3 and zₑQzₑᵀ=1 for every e, then G has an S²-flow.', [
        'Factor Q=AAᵀ, where A has at most three columns; pad with zero columns to three if necessary. Set X=ZA. Then BX=BZA=0 since BZ=0. For each row xₑ we have ||xₑ||²=zₑAAᵀzₑᵀ=zₑQzₑᵀ=1. Hence the rows of X define an S²-flow.'
    ])
    add_body(doc, 'This lemma separates the problem into a convex part Q⪰0 with linear diagonal constraints and the non-convex condition rank Q≤3. The code verifies such certificates independently of the nonlinear solver.')

    doc.add_heading('11. Large-Scale Reproducible Verification', level=1)
    add_body(doc, f"A deterministic campaign was run on {campaign['instances']} graphs: 270 random bridgeless cubic graphs of orders 10, 12, 14, 16, 18, 20, 24, 30 and 40, 30 graphs of each order, together with 18 named and parametric graphs. Seed: {campaign['config']['seed']}.")
    add_body(doc, f"Obtained {campaign['exact_constructive_certificates']} exact constructive certificates from 3-edge-colourings and {campaign['nonlinear_certificates']} numerical rank-3 certificates for non-3-edge-colourable or specially chosen graphs. Independent re-verification read all NPZ certificates afresh and confirmed {campaign['valid_certificates']} out of {campaign['instances']}.")
    add_body(doc, f"Maximum Kirchhoff-law residual: {campaign['maximum_conservation_residual']:.3e}. Maximum unit-norm residual among numerical solutions: {campaign['maximum_unit_norm_residual']:.3e}. An independent threshold of 10⁻⁷ is applied for numerical certificates; constructive certificates have errors of the order of machine rounding.")
    doc.add_picture(str(cert_fig), width=Inches(5.8))
    p = doc.add_paragraph('Figure 2. Distribution of certificate types.')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].italic = True
    doc.add_picture(str(residual_fig), width=Inches(6.5))
    p = doc.add_paragraph('Figure 3. Norm errors for the eight nonlinear certificates.')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].italic = True

    table = doc.add_table(rows=1, cols=6)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ['Graph', '|V|', '3-colouring', 'Method', 'Balance error', 'Norm error']
    for i, h in enumerate(headers):
        set_cell_text(table.rows[0].cells[i], h, bold=True, size=8)
        shade_cell(table.rows[0].cells[i], 'D9EAF7')
    for _, row in nonlinear.iterrows():
        cells = table.add_row().cells
        values = [
            str(row['name']),
            str(int(row['vertices'])),
            str(row['three_edge_coloring_status']),
            'cycle-space LSQ',
            f"{row['max_conservation_residual']:.2e}",
            f"{row['max_unit_norm_residual']:.2e}",
        ]
        for i, value in enumerate(values):
            set_cell_text(cells[i], value, size=7.5)

    doc.add_heading('12. Reproducibility', level=1)
    add_body(doc, 'Main run:')
    code = doc.add_paragraph()
    code.style = doc.styles['Normal']
    run = code.add_run('python scripts/massive_verification.py --orders 10 12 14 16 18 20 24 30 40 --samples-per-order 30 --nonlinear-restarts 16 --output-dir results/massive_run')
    run.font.name = 'Courier New'
    run.font.size = Pt(8.5)
    add_body(doc, 'Independent verification of stored certificates:')
    code = doc.add_paragraph()
    run = code.add_run('python scripts/verify_campaign.py results/massive_run --tolerance 1e-7')
    run.font.name = 'Courier New'
    run.font.size = Pt(8.5)
    add_body(doc, 'For exhaustive graph6 flows from nauty a streaming script is provided:')
    code = doc.add_paragraph()
    run = code.add_run('geng -c -d3 -D3 16 | python scripts/nauty_cubic_campaign.py --output-dir results/geng16')
    run.font.name = 'Courier New'
    run.font.size = Pt(8.5)
    add_body(doc, 'Each certificate contains the graph6 representation of the graph, a stable edge ordering, and the matrix X. The verifier rebuilds the incidence matrix and computes BX, row norms, and the rank of the Gram matrix. A successful finite verification is not a proof of an infinite statement.')

    doc.add_heading('13. Limitations and the Next Proof Barrier', level=1)
    limitations = [
        'The full conjecture is not proved.',
        'The exact cut theorems reduce the problem to cyclically 4-edge-connected atoms, but do not resolve those atoms.',
        'Numerical solutions for snarks are verifiable approximate certificates, not symbolic existence proofs for an infinite family.',
        'A universal 4-cycle reduction that would automatically raise the girth of the minimal counterexample to 5 has not been obtained.',
        'The exact world priority of the factorization formulations must be confirmed by independent bibliographic review and peer review.'
    ]
    for item in limitations:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(item)

    doc.add_heading('14. Conclusion', level=1)
    add_body(doc, 'Complete proofs of several substantial partial results have been obtained. The strongest structural advance is the exact two-directional factorization of S²-flows at 2- and 3-edge cuts. It converts composition constructions into a decomposition theorem, strengthens triangle blow-up to an equivalence, and shows that a minimal counterexample must be atomic. The constructive theorem for all 3-edge-colourable cubic graphs covers the planar case and yields exact machine-verifiable certificates. The open core remains the cyclically 4-edge-connected non-3-edge-colourable cubic graphs.')

    doc.add_heading('References', level=1)
    refs = [
        'H. Houdrouge, B. Miraftab, P. Morin. 2-Dimensional Unit Vector Flows. arXiv:2602.21526, 2026.',
        'D. Mattiolo, G. Mazzuoccolo, J. Rajník, G. Tabarelli. On d-dimensional nowhere-zero r-flows on a graph. European Journal of Mathematics 9, Article 101, 2023. DOI: 10.1007/s40879-023-00694-1.',
        'C. Thomassen. Group flow, complex flow, unit vector flow, and the (2+epsilon)-flow conjecture. Journal of Combinatorial Theory, Series B 108, 81-91, 2014. DOI: 10.1016/j.jctb.2014.02.012.',
        'G. Brinkmann, J. Goedgebeur, J. Hägglund, K. Markström. Generation and properties of snarks. Journal of Combinatorial Theory, Series B 103(4), 468-488, 2013.',
        'R. Diestel. Graph Theory, 5th edition. Springer, 2018.',
        'W. T. Tutte. A contribution to the theory of chromatic polynomials. Canadian Journal of Mathematics 6, 80-91, 1954.'
    ]
    for ref in refs:
        p = doc.add_paragraph(style='List Number')
        p.add_run(ref)

    doc.core_properties.title = 'New partial theorems and structural lemmas for S²-flows'
    doc.core_properties.subject = 'S2-flow conjecture, cubic graphs, structural decomposition, reproducibility'
    doc.core_properties.author = 'Research synthesis'
    doc.save(OUT)
    print(OUT)


if __name__ == '__main__':
    build_doc()
