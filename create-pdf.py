from fpdf import FPDF

# Create a new PDF instance
pdf = FPDF()
pdf.add_page()
pdf.set_font("Courier", size=12)

# Write lines to the PDF
lines = [
    "Order #272 for Bryson",
    "",
    "----- Delivery details ------",
    "Driver: Barry Potmore",
    "Address: 123 Main St",
    "Postcode: 4000",
    "Ph.: 0412 345 678",
    "",
    "------- Order details -------",
    "3 x Hawaiian           $29.99",
    "1 x Pepperoni          $10.00",
    "                     --------",
    "Subtotal               $39.99",
    "Delivery fee            $3.99",
    "                     --------",
    "Total                  $43.98"
]

for line in lines:
    pdf.cell(200, 10, txt=line, ln=True)

# Save the PDF
pdf.output("simple_example.pdf")