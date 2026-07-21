"""Build the English rigorous equivariance addendum as a Word document."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"
OUTPUT = DOCS / "S2_flow_equivariance_rigorous_addendum_en.docx"


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), fill)
    tc_pr.append(shading)


def set_cell_text(cell, text: str, bold: bool = False, size: float = 8.5) -> None:
    cell.text = ""
    paragraph = cell.paragraphs[0]
    run = paragraph.add_run(text)
    run.bold = bold
    run.font.name = "Arial"
    run.font.size = Pt(size)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def add_equation(document: Document, text: str) -> None:
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run(text)
    run.font.name = "Cambria Math"
    run.font.size = Pt(11)


def add_bullet(document: Document, text: str) -> None:
    paragraph = document.add_paragraph(style="List Bullet")
    paragraph.add_run(text)


def configure_document(document: Document) -> None:
    section = document.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)

    styles = document.styles
    normal = styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(10)
    normal.paragraph_format.space_after = Pt(5)
    normal.paragraph_format.line_spacing = 1.08

    for name, size in (("Title", 24), ("Subtitle", 12), ("Heading 1", 16), ("Heading 2", 13), ("Heading 3", 11)):
        style = styles[name]
        style.font.name = "Arial"
        style.font.size = Pt(size)
        style.font.bold = name != "Subtitle"


def create_figures(generator_records: list[dict], certificate_records: list[dict]) -> tuple[Path, Path]:
    ASSETS.mkdir(parents=True, exist_ok=True)
    ns = [5, 7, 9, 11, 13]
    residual_min = []
    residual_max = []
    deficit_max = []
    for n in ns:
        rows = [row for row in generator_records if row["n"] == n]
        residual_min.append(min(row["equivariance_residual_max"] for row in rows))
        residual_max.append(max(row["equivariance_residual_max"] for row in rows))
        deficit_max.append(max(row["averaged_norm_deficit_max"] for row in rows))

    figure_one = ASSETS / "all_generator_diagnostics.png"
    plt.figure(figsize=(7.2, 3.8))
    plt.plot(ns, residual_min, marker="o", label="Minimum equivariance residual")
    plt.plot(ns, residual_max, marker="o", label="Maximum equivariance residual")
    plt.plot(ns, deficit_max, marker="s", label="Maximum averaged norm deficit")
    plt.xlabel("Flower parameter n")
    plt.ylabel("Residual or deficit")
    plt.ylim(0, 2.05)
    plt.xticks(ns)
    plt.grid(True, alpha=0.25)
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(figure_one, dpi=180)
    plt.close()

    figure_two = ASSETS / "exact_certificate_bounds.png"
    cert_ns = [record["vertices"] // 4 for record in certificate_records]
    contractions = [record["contraction_bound"] for record in certificate_records]
    radii = [-record["radii_polynomial"] for record in certificate_records]
    plt.figure(figsize=(7.2, 3.8))
    plt.semilogy(cert_ns, contractions, marker="o", label="Contraction bound")
    plt.semilogy(cert_ns, radii, marker="s", label="Negative radii-polynomial margin")
    plt.xlabel("Flower parameter n")
    plt.ylabel("Verified bound")
    plt.xticks(cert_ns[::2])
    plt.grid(True, alpha=0.25)
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(figure_two, dpi=180)
    plt.close()
    return figure_one, figure_two


def add_title_page(document: Document) -> None:
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.space_after = Pt(18)
    run = paragraph.add_run("Rigorous Equivariance Addendum for Flower-Snark S²-Flows")
    run.bold = True
    run.font.name = "Arial"
    run.font.size = Pt(24)

    subtitle = document.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run(
        "Exact exclusion of the strict order-2n ansatz, complete all-generator diagnostics, "
        "and independently verifiable dyadic Newton-Kantorovich certificates for J5-J41"
    )
    run.font.name = "Arial"
    run.font.size = Pt(12)

    document.add_paragraph()
    status = document.add_paragraph()
    status.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = status.add_run("Reproducibility package revision - 19 July 2026")
    run.italic = True
    run.font.name = "Arial"
    run.font.size = Pt(10)

    document.add_page_break()


def add_remediation_summary(document: Document) -> None:
    document.add_heading("1. Executive summary and corrected status", level=1)
    document.add_paragraph(
        "This revision removes the three material caveats identified in the first equivariance addendum. "
        "The strict one-block ansatz is now excluded by a complete analytic proof for every odd flower "
        "parameter, the exact finite-range existence theorem is backed by the actual machine-readable "
        "certificates and an independent verifier, and the asymmetry test now covers every cyclic generator."
    )

    table = document.add_table(rows=1, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    headers = ["Earlier caveat", "Resolution", "Proof status", "Reproducible artifact"]
    for index, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[index], header, bold=True, size=8.2)
        set_cell_shading(table.rows[0].cells[index], "D9EAF7")
    rows = [
        (
            "Strict Z_2n nonexistence was inferred from local optimisation.",
            "A structural contradiction is proved for both det(Q)=+1 and det(Q)=-1.",
            "Exact theorem for all odd n >= 5.",
            "strict_ansatz_exact.py",
        ),
        (
            "The claimed rational certificates were absent.",
            "Nineteen dyadic certificates for J5-J41 and a separate integer-only verifier are included.",
            "Exact computer-assisted theorem for the finite range.",
            "certificates/*.npz and verify_exact_certificates.py",
        ),
        (
            "Only one generator was evaluated in the supplied code.",
            "All exponents coprime to 2n are tested; the averaging pullback is corrected.",
            "Validated numerical diagnostic over 38 generators.",
            "equivariance_all_generators.py",
        ),
    ]
    for row_values in rows:
        cells = table.add_row().cells
        for index, value in enumerate(row_values):
            set_cell_text(cells[index], value, size=7.8)

    document.add_paragraph()
    note = document.add_paragraph()
    run = note.add_run("Important correction. ")
    run.bold = True
    note.add_run(
        "The earlier group-average implementation used the wrong matrix power in row-vector convention. "
        "After correction, the stored certificates remain strongly non-equivariant, but the J5 averaged "
        "norm deficit is approximately 0.60 rather than 0.99. The scientific conclusion survives; the "
        "previous numerical value does not."
    )


def add_strict_theorem(document: Document) -> None:
    document.add_heading("2. Exact exclusion of the strict order-2n ansatz", level=1)
    paragraph = document.add_paragraph()
    run = paragraph.add_run("Theorem 1 (strict one-block equivariance is impossible). ")
    run.bold = True
    paragraph.add_run(
        "For every odd n >= 5, no unit S²-flow on the flower snark J_n is equivariant under the full "
        "one-block automorphism sigma of order 2n through a single matrix Q in O(3)."
    )

    document.add_heading("2.1 Canonical reduction", level=2)
    document.add_paragraph(
        "Orient the four edge types as A_i: c_i -> t_i, B_i: t_i -> t_(i+1), "
        "C_j: c_(j mod n) -> w_j, and D_j: w_j -> w_(j+1). Reorientation changes only signs and therefore "
        "does not affect existence. Strict equivariance gives four unit templates a, b, c, d such that"
    )
    add_equation(document, "A_i = Q^i a,   B_i = Q^i b,   C_j = Q^j c,   D_j = Q^j d.")
    document.add_paragraph("Kirchhoff's law at t_i, w_j, and c_i reduces exactly to")
    add_equation(document, "a = (I - Q^(-1)) b,     c = (I - Q^(-1)) d,     a + (I + Q^n)c = 0.")
    document.add_paragraph("Orbit closure adds")
    add_equation(document, "Q^n a = a,   Q^n b = b,   Q^(2n)c = c,   Q^(2n)d = d,")
    document.add_paragraph("with |a|=|b|=|c|=|d|=1.")

    document.add_heading("2.2 Proper orthogonal case", level=2)
    document.add_paragraph(
        "Assume det(Q)=+1. Then Q is a rotation. The equation a=(I-Q^(-1))b and |a|=1 show that b is not "
        "fixed by Q. Since Q^n b=b, Q^n cannot be a nontrivial rotation, whose fixed space is only its axis; "
        "otherwise b would lie on that axis and a would vanish. Hence Q^n=I. The hub equation becomes "
        "a+2c=0, which is impossible because both vectors have unit norm."
    )

    document.add_heading("2.3 Improper orthogonal case", level=2)
    document.add_paragraph(
        "Assume det(Q)=-1. Orthogonally decompose R^3=P direct-sum L so that Q is a planar rotation through "
        "theta on P and multiplication by -1 on L. Because n is odd and Q^n b=b, the L-component of b is "
        "zero. A nonzero planar fixed vector of Q^n also forces n theta to be a multiple of 2 pi."
    )
    add_equation(document, "lambda = 4 sin^2(theta/2).")
    document.add_paragraph(
        "For a planar vector u, |(I-Q^(-1))u|^2=lambda |u|^2. Applying this to a=(I-Q^(-1))b and the unit "
        "norms yields lambda=1. Now Q^n is +I on P and -I on L. The hub equation forces"
    )
    add_equation(document, "|c_P|^2 = 1/4,     |c_L|^2 = 3/4.")
    document.add_paragraph(
        "Since c=(I-Q^(-1))d, one has c_L=2d_L. Therefore |d_L|^2=3/16 and |d_P|^2=13/16. Consequently"
    )
    add_equation(document, "|c|^2 = lambda |d_P|^2 + 4|d_L|^2 = 13/16 + 12/16 = 25/16,")
    document.add_paragraph(
        "contradicting |c|=1. Both determinant cases are impossible, completing the proof. The accompanying "
        "SymPy script verifies the only scalar arithmetic step exactly: 25/16 - 1 = 9/16."
    )


def add_generator_analysis(document: Document, records: list[dict], figure: Path) -> None:
    document.add_heading("3. All-generator equivariance diagnostic", level=1)
    document.add_paragraph(
        "For each J_n in {5,7,9,11,13}, every exponent r coprime to 2n is evaluated. The transported "
        "automorphism tau_r=sigma^r is lifted to the oriented edge list, including orientation signs. A proper "
        "rotation R_r is fitted by orthogonal Procrustes analysis."
    )
    add_equation(
        document,
        "epsilon_r = max_e | s_e x_(tau_r(e)) - R_r x_e |.",
    )
    document.add_paragraph("The corrected cyclic diagnostic average is")
    add_equation(
        document,
        "xbar_e = (1/(2n)) sum_(k=0)^(2n-1) R_r^(-k) [s_e^(k) x_(tau_r^k(e))].",
    )
    document.add_paragraph(
        "In the row-vector implementation, the pullback is right multiplication by R_r^k. The complete "
        "pipeline is validated on synthetically planted equivariant data: the worst rotation recovery error is "
        "1.43e-15, the worst equivariance residual is 1.27e-15, and the worst averaging reconstruction error is "
        "6.21e-15."
    )

    table = document.add_table(rows=1, cols=6)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Graph", "Generators", "Residual min", "Residual max", "Norm deficit max", "Kirchhoff max"]
    for index, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[index], header, bold=True, size=8)
        set_cell_shading(table.rows[0].cells[index], "D9EAF7")
    for n in [5, 7, 9, 11, 13]:
        rows = [row for row in records if row["n"] == n]
        values = [
            f"J{n}",
            str(len(rows)),
            f"{min(row['equivariance_residual_max'] for row in rows):.3f}",
            f"{max(row['equivariance_residual_max'] for row in rows):.3f}",
            f"{max(row['averaged_norm_deficit_max'] for row in rows):.3f}",
            f"{max(row['averaged_kirchhoff_residual'] for row in rows):.2e}",
        ]
        cells = table.add_row().cells
        for index, value in enumerate(values):
            set_cell_text(cells[index], value, size=8)

    document.add_picture(str(figure), width=Inches(6.7))
    caption = document.add_paragraph("Figure 1. Diagnostics over all 38 cyclic generators.")
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption.runs[0].italic = True
    document.add_paragraph(
        "Conclusion. Every stored certificate is far from every tested equivariant representation, with even "
        "the best generator giving a maximum edge residual between 1.802 and 1.948. This is a statement about "
        "the particular generic Newton certificates, not about the existence of a separate Z_n-symmetric branch."
    )


def add_certification(document: Document, records: list[dict], figure: Path) -> None:
    document.add_heading("4. Complete exact certificates for J5-J41", level=1)
    paragraph = document.add_paragraph()
    run = paragraph.add_run("Theorem 2 (finite certified flower family). ")
    run.bold = True
    paragraph.add_run(
        "For every odd n with 5 <= n <= 41, the flower snark J_n admits an exact S²-flow."
    )

    document.add_heading("4.1 Rational polynomial system", level=2)
    document.add_paragraph(
        "Let B be the oriented incidence matrix and let Z be an integer fundamental-cycle basis of ker(B), "
        "with q=m-v+1=2n+1 columns. Every three-dimensional flow is X=ZY for a q by 3 coefficient matrix Y. "
        "The 6n unit equations are"
    )
    add_equation(document, "f_e(Y) = |(ZY)_e|^2 - 1 = 0,     e=1,...,6n.")
    document.add_paragraph(
        "Three linear gauge equations place one selected edge on the x-axis and a second nonparallel edge in "
        "the xy-plane. Thus the system has 6n+3 equations in 3q=6n+3 variables and entirely integer coefficients."
    )

    document.add_heading("4.2 Exact Newton-Kantorovich inequality", level=2)
    document.add_paragraph(
        "The certificate stores dyadic rational approximations y0 and A to a solution and the inverse Jacobian. "
        "Using the infinity norm, the verifier computes exactly"
    )
    add_equation(document, "alpha = |A F(y0)|,   beta = |I - A J(y0)|,   |A(J(y)-J(y0))| <= L |y-y0|.")
    document.add_paragraph("For r=10^(-8), it verifies the radii polynomial and contraction inequalities")
    add_equation(document, "p(r) = alpha + (beta - 1)r + Lr^2 < 0,     beta + Lr < 1.")
    document.add_paragraph(
        "Banach's fixed-point theorem then gives a unique exact root in the closed infinity-norm ball of radius r. "
        "Because BZ=0 exactly and all norm equations vanish at the root, the resulting object is an exact S²-flow. "
        "All decisive products and inequalities are recomputed with arbitrary-precision integers by the independent "
        "verifier; SciPy is not imported by that verifier."
    )

    table = document.add_table(rows=1, cols=7)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["J_n", "Dimension", "alpha", "beta", "L", "p(r)", "Contraction"]
    for index, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[index], header, bold=True, size=7.5)
        set_cell_shading(table.rows[0].cells[index], "D9EAF7")
    for record in records:
        n = record["vertices"] // 4
        values = [
            f"J{n}",
            str(record["dimension"]),
            f"{record['alpha']:.2e}",
            f"{record['beta']:.2e}",
            f"{record['lipschitz']:.2e}",
            f"{record['radii_polynomial']:.2e}",
            f"{record['contraction_bound']:.2e}",
        ]
        cells = table.add_row().cells
        for index, value in enumerate(values):
            set_cell_text(cells[index], value, size=7.1)

    document.add_picture(str(figure), width=Inches(6.7))
    caption = document.add_paragraph("Figure 2. Exact certificate margins for all nineteen flower snarks.")
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption.runs[0].italic = True

    document.add_paragraph(
        "The earlier value r=10^(-6) is not retained. The present verifier uses a deliberately conservative "
        "global infinity-norm Lipschitz bound, for which r=10^(-8) succeeds uniformly through J41. This is a "
        "change in certificate radius, not a weakening of the existence theorem."
    )


def add_reproducibility(document: Document) -> None:
    document.add_heading("5. Reproducibility map", level=1)
    table = document.add_table(rows=1, cols=2)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for index, header in enumerate(["Artifact", "Purpose"]):
        set_cell_text(table.rows[0].cells[index], header, bold=True, size=8.5)
        set_cell_shading(table.rows[0].cells[index], "D9EAF7")
    entries = [
        ("scripts/strict_ansatz_exact.py", "Exact symbolic audit of the all-n strict-ansatz contradiction."),
        ("scripts/equivariance_all_generators.py", "All 38 generators, corrected averaging, and synthetic validation."),
        ("scripts/zn_ansatz.py", "Rebuilds the six-template k=1 numerical branch from J5 through J41."),
        ("scripts/exact_rational_certificates.py", "Builds dyadic Newton-Kantorovich certificates."),
        ("scripts/verify_exact_certificates.py", "Independent arbitrary-integer verification of every certificate."),
        ("scripts/verify_all.py", "Runs the full exact, numerical, and regression test suite."),
        ("certificates/*.npz", "Nineteen complete certificates, including inverse-Jacobian data."),
        ("results/*.json and *.csv", "Machine-readable outputs used in this report."),
    ]
    for artifact, purpose in entries:
        cells = table.add_row().cells
        set_cell_text(cells[0], artifact, size=8)
        set_cell_text(cells[1], purpose, size=8)

    document.add_paragraph("Complete verification command:")
    paragraph = document.add_paragraph()
    run = paragraph.add_run("python -m pip install -r requirements.txt\npython scripts/verify_all.py")
    run.font.name = "Courier New"
    run.font.size = Pt(9)


def add_remaining_scope(document: Document) -> None:
    document.add_heading("6. Remaining all-n problem", level=1)
    document.add_paragraph(
        "The finite theorem through J41 and the exact exclusion of the strict Z_2n ansatz do not yet prove the "
        "existence of a Z_n-equivariant S²-flow for every odd n. The remaining target is a uniform existence theorem "
        "for the reduced six-template system F(z,theta)=0 over theta in (0,2pi/5], where theta=2pi/n. The most "
        "direct rigorous routes are interval continuation with a finite Kantorovich mesh plus derivative bounds, or "
        "a symbolic parametrisation of the observed k=1 branch. No statement in this document treats the numerical "
        "smoothness evidence as an all-n proof."
    )


def main() -> None:
    generator_payload = json.loads((ROOT / "results/equivariance_all_generators.json").read_text())
    generator_records = generator_payload["results"]
    certificate_records = json.loads((ROOT / "results/independent_exact_verification.json").read_text())
    certificate_records.sort(key=lambda record: record["vertices"])
    figure_one, figure_two = create_figures(generator_records, certificate_records)

    document = Document()
    configure_document(document)
    add_title_page(document)
    add_remediation_summary(document)
    add_strict_theorem(document)
    add_generator_analysis(document, generator_records, figure_one)
    add_certification(document, certificate_records, figure_two)
    add_reproducibility(document)
    add_remaining_scope(document)

    DOCS.mkdir(parents=True, exist_ok=True)
    document.save(OUTPUT)
    print(f"Saved {OUTPUT}")


if __name__ == "__main__":
    main()
