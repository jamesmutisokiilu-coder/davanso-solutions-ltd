import os
from io import BytesIO
from datetime import datetime, date
from decimal import Decimal, InvalidOperation

from flask import (
    Flask,
    render_template,
    request,
    send_file,
    redirect,
    url_for,
    flash,
    jsonify,
)

from flask_sqlalchemy import SQLAlchemy

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)


# ============================================================
# DAVANSO SOLUTIONS LTD
# AUTOMATED BUSINESS MANAGEMENT SYSTEM
# RENDER READY VERSION
# ============================================================


app = Flask(
    __name__,
    static_folder="static",
    static_url_path="/static",
    template_folder="templates",
)


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "davanso-solutions-secret-key-change-this"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# ============================================================
# DATABASE CONFIGURATION
# ============================================================
#
# Render provides DATABASE_URL when PostgreSQL is connected.
#
# Locally:
#     SQLite will be used automatically.
#
# Render:
#     PostgreSQL will be used automatically.
#


database_url = os.environ.get("DATABASE_URL")


if database_url:

    # Render / some providers may provide postgres://
    # SQLAlchemy expects postgresql://

    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql://",
            1
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url

else:

    # Local development fallback.
    #
    # Flask-SQLAlchemy stores this database under
    # the Flask instance folder.

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///davanso_business.db"
    )


db = SQLAlchemy(app)


# ============================================================
# COMPANY INFORMATION
# ============================================================

COMPANY_NAME = "DAVANSO SOLUTIONS LTD"

COMPANY_TAGLINE = (
    "Engineering • Energy • Water • Electrical"
)

COMPANY_PHONE = "+254 700 000 000"

COMPANY_EMAIL = (
    "info@davansosolutions.co.ke"
)

COMPANY_SALES_EMAIL = (
    "sales@davansosolutions.co.ke"
)

COMPANY_LOCATION = "Kenya"

COMPANY_WEBSITE = (
    "www.davansosolutions.co.ke"
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def clean(value):
    """
    Clean submitted form values.
    """

    if value is None:
        return ""

    return str(value).strip()


def money(value):
    """
    Safely convert a value into Decimal.
    """

    try:

        if value is None:
            return Decimal("0.00")

        value = (
            str(value)
            .replace(",", "")
            .strip()
        )

        if value == "":
            return Decimal("0.00")

        return Decimal(value)

    except (
        InvalidOperation,
        ValueError,
        TypeError,
    ):

        return Decimal("0.00")


def format_money(value):
    """
    Format money as Kenyan Shillings.
    """

    value = money(value)

    return f"KSh {value:,.2f}"


def today():
    """
    Return today's date.
    """

    return date.today()


def now():
    """
    Return current date/time.
    """

    return datetime.now()


def generate_number(prefix):
    """
    Automatically generate unique document numbers.
    """

    return (
        f"{prefix}-"
        f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    )


# ============================================================
# DATABASE MODELS
# ============================================================


class Customer(db.Model):

    __tablename__ = "customers"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(200),
        nullable=False
    )

    phone = db.Column(
        db.String(50)
    )

    email = db.Column(
        db.String(200)
    )

    address = db.Column(
        db.String(300)
    )

    location = db.Column(
        db.String(200)
    )

    created_at = db.Column(
        db.DateTime,
        default=now
    )


class Product(db.Model):

    __tablename__ = "products"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(200),
        nullable=False
    )

    category = db.Column(
        db.String(100)
    )

    description = db.Column(
        db.Text
    )

    purchase_price = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    selling_price = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    stock_quantity = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    minimum_stock = db.Column(
        db.Numeric(12, 2),
        default=5
    )

    unit = db.Column(
        db.String(50),
        default="pcs"
    )

    created_at = db.Column(
        db.DateTime,
        default=now
    )

    updated_at = db.Column(
        db.DateTime,
        default=now,
        onupdate=now
    )


class StockMovement(db.Model):

    __tablename__ = "stock_movements"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False
    )

    movement_type = db.Column(
        db.String(50),
        nullable=False
    )

    quantity = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    unit_cost = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    total_cost = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    reference = db.Column(
        db.String(100)
    )

    notes = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=now
    )

    product = db.relationship(
        "Product",
        backref="stock_movements"
    )


class Sale(db.Model):

    __tablename__ = "sales"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    sale_number = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customers.id")
    )

    total_amount = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    total_cost = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    profit = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    payment_method = db.Column(
        db.String(50),
        default="Cash"
    )

    created_at = db.Column(
        db.DateTime,
        default=now
    )

    customer = db.relationship(
        "Customer",
        backref="sales"
    )


class SaleItem(db.Model):

    __tablename__ = "sale_items"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    sale_id = db.Column(
        db.Integer,
        db.ForeignKey("sales.id"),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False
    )

    quantity = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    purchase_price = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    selling_price = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    total = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    cost = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    profit = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    sale = db.relationship(
        "Sale",
        backref="items"
    )

    product = db.relationship(
        "Product"
    )


class Quotation(db.Model):

    __tablename__ = "quotations"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    quotation_number = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customers.id")
    )

    project_type = db.Column(
        db.String(150)
    )

    project_location = db.Column(
        db.String(300)
    )

    subtotal = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    total_cost = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    estimated_profit = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    validity = db.Column(
        db.String(100),
        default="30 Days"
    )

    notes = db.Column(
        db.Text
    )

    terms = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=now
    )

    customer = db.relationship(
        "Customer",
        backref="quotations"
    )


class QuotationItem(db.Model):

    __tablename__ = "quotation_items"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    quotation_id = db.Column(
        db.Integer,
        db.ForeignKey("quotations.id"),
        nullable=False
    )

    product_name = db.Column(
        db.String(300),
        nullable=False
    )

    quantity = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    purchase_price = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    unit_price = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    total = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    cost = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    profit = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    quotation = db.relationship(
        "Quotation",
        backref="items"
    )


class Expense(db.Model):

    __tablename__ = "expenses"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    description = db.Column(
        db.String(300),
        nullable=False
    )

    amount = db.Column(
        db.Numeric(12, 2),
        default=0
    )

    category = db.Column(
        db.String(100)
    )

    created_at = db.Column(
        db.DateTime,
        default=now
    )


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

with app.app_context():

    db.create_all()


# ============================================================
# MAIN DASHBOARD
# ============================================================


@app.route("/")
def index():

    products = Product.query.all()

    customers_count = (
        Customer.query.count()
    )

    products_count = (
        Product.query.count()
    )

    sales_count = (
        Sale.query.count()
    )

    quotation_count = (
        Quotation.query.count()
    )

    total_sales = sum(
        (
            money(s.total_amount)
            for s in Sale.query.all()
        ),
        Decimal("0.00")
    )

    total_profit = sum(
        (
            money(s.profit)
            for s in Sale.query.all()
        ),
        Decimal("0.00")
    )

    total_expenses = sum(
        (
            money(e.amount)
            for e in Expense.query.all()
        ),
        Decimal("0.00")
    )

    stock_value = sum(
        (
            money(p.stock_quantity)
            * money(p.purchase_price)
            for p in products
        ),
        Decimal("0.00")
    )

    low_stock = [
        p
        for p in products
        if money(p.stock_quantity)
        <= money(p.minimum_stock)
    ]

    return render_template(
        "index.html",
        products=products,
        customers_count=customers_count,
        products_count=products_count,
        sales_count=sales_count,
        quotation_count=quotation_count,
        total_sales=total_sales,
        total_profit=total_profit,
        total_expenses=total_expenses,
        stock_value=stock_value,
        low_stock=low_stock,
    )


# ============================================================
# DASHBOARD ALIAS
# ============================================================


@app.route("/dashboard")
def dashboard():

    return redirect(
        url_for("index")
    )


# ============================================================
# HEALTH CHECK
# ============================================================


@app.route("/health")
def health():

    try:

        db.session.execute(
            db.text("SELECT 1")
        )

        return jsonify({
            "status": "healthy",
            "application": "Davanso Solutions Ltd",
            "database": "connected"
        }), 200

    except Exception as error:

        return jsonify({
            "status": "unhealthy",
            "error": str(error)
        }), 500


# ============================================================
# ABOUT
# ============================================================


@app.route("/about")
def about():

    return render_template(
        "about.html"
    )


# ============================================================
# SERVICES
# ============================================================


@app.route("/services")
def services():

    return render_template(
        "services.html"
    )


# ============================================================
# PROJECTS
# ============================================================


@app.route("/projects")
def projects():

    return render_template(
        "projects.html"
    )


# ============================================================
# PRODUCTS
# ============================================================


@app.route("/products")
def products():

    products = Product.query.order_by(
        Product.name.asc()
    ).all()

    return render_template(
        "products.html",
        products=products
    )


# ============================================================
# CONTACT
# ============================================================


@app.route("/contact")
def contact():

    return render_template(
        "contact.html"
    )


# ============================================================
# CUSTOMERS
# ============================================================


@app.route("/customers")
def customers():

    customers = Customer.query.order_by(
        Customer.created_at.desc()
    ).all()

    return render_template(
        "customers.html",
        customers=customers
    )


# ============================================================
# ADD CUSTOMER
# ============================================================


@app.route(
    "/add-customer",
    methods=["POST"]
)
def add_customer():

    customer = Customer(

        name=clean(
            request.form.get("name")
        ),

        phone=clean(
            request.form.get("phone")
        ),

        email=clean(
            request.form.get("email")
        ),

        address=clean(
            request.form.get("address")
        ),

        location=clean(
            request.form.get("location")
        )
    )

    if not customer.name:

        flash(
            "Customer name is required.",
            "error"
        )

        return redirect(
            url_for("customers")
        )

    db.session.add(customer)

    db.session.commit()

    flash(
        "Customer saved successfully.",
        "success"
    )

    return redirect(
        url_for("customers")
    )


# ============================================================
# INVENTORY
# ============================================================


@app.route("/inventory")
def inventory():

    products = Product.query.order_by(
        Product.name.asc()
    ).all()

    low_stock = [
        p
        for p in products
        if money(p.stock_quantity)
        <= money(p.minimum_stock)
    ]

    return render_template(
        "inventory.html",
        products=products,
        low_stock=low_stock
    )


# ============================================================
# ADD PRODUCT
# ============================================================


@app.route(
    "/add-product",
    methods=["POST"]
)
def add_product():

    name = clean(
        request.form.get("name")
    )

    category = clean(
        request.form.get("category")
    )

    description = clean(
        request.form.get("description")
    )

    purchase_price = money(
        request.form.get(
            "purchase_price"
        )
    )

    selling_price = money(
        request.form.get(
            "selling_price"
        )
    )

    quantity = money(
        request.form.get(
            "quantity"
        )
    )

    minimum_stock = money(
        request.form.get(
            "minimum_stock"
        )
    )

    unit = clean(
        request.form.get("unit")
    ) or "pcs"

    if not name:

        flash(
            "Product name is required.",
            "error"
        )

        return redirect(
            url_for("inventory")
        )

    product = Product(

        name=name,

        category=category,

        description=description,

        purchase_price=purchase_price,

        selling_price=selling_price,

        stock_quantity=quantity,

        minimum_stock=minimum_stock,

        unit=unit
    )

    db.session.add(product)

    db.session.flush()

    if quantity > 0:

        movement = StockMovement(

            product_id=product.id,

            movement_type="STOCK IN",

            quantity=quantity,

            unit_cost=purchase_price,

            total_cost=(
                quantity
                * purchase_price
            ),

            reference="INITIAL STOCK",

            notes=(
                "Initial stock automatically recorded."
            )
        )

        db.session.add(movement)

    db.session.commit()

    flash(
        "Product and stock saved successfully.",
        "success"
    )

    return redirect(
        url_for("inventory")
    )


# ============================================================
# STOCK IN
# ============================================================


@app.route(
    "/stock-in",
    methods=["POST"]
)
def stock_in():

    product_id = request.form.get(
        "product_id"
    )

    quantity = money(
        request.form.get(
            "quantity"
        )
    )

    purchase_price = money(
        request.form.get(
            "purchase_price"
        )
    )

    reference = clean(
        request.form.get(
            "reference"
        )
    )

    notes = clean(
        request.form.get(
            "notes"
        )
    )

    product = Product.query.get(
        product_id
    )

    if not product:

        flash(
            "Product not found.",
            "error"
        )

        return redirect(
            url_for("inventory")
        )

    if quantity <= 0:

        flash(
            "Stock quantity must be greater than zero.",
            "error"
        )

        return redirect(
            url_for("inventory")
        )

    if purchase_price > 0:

        product.purchase_price = (
            purchase_price
        )

    product.stock_quantity = (
        money(product.stock_quantity)
        + quantity
    )

    movement = StockMovement(

        product_id=product.id,

        movement_type="STOCK IN",

        quantity=quantity,

        unit_cost=(
            purchase_price
            if purchase_price > 0
            else money(
                product.purchase_price
            )
        ),

        total_cost=(
            quantity
            * (
                purchase_price
                if purchase_price > 0
                else money(
                    product.purchase_price
                )
            )
        ),

        reference=reference,

        notes=notes
    )

    db.session.add(movement)

    db.session.commit()

    flash(
        f"{quantity:,.2f} {product.unit} "
        f"of {product.name} added to stock.",
        "success"
    )

    return redirect(
        url_for("inventory")
    )


# ============================================================
# STOCK MOVEMENTS
# ============================================================


@app.route("/stock-movements")
def stock_movements():

    movements = StockMovement.query.order_by(
        StockMovement.created_at.desc()
    ).all()

    return render_template(
        "stock_movements.html",
        movements=movements
    )


# ============================================================
# SALES
# ============================================================


@app.route("/sales")
def sales():

    sales = Sale.query.order_by(
        Sale.created_at.desc()
    ).all()

    products = Product.query.order_by(
        Product.name.asc()
    ).all()

    customers = Customer.query.order_by(
        Customer.name.asc()
    ).all()

    return render_template(
        "sales.html",
        sales=sales,
        products=products,
        customers=customers
    )


# ============================================================
# RECORD SALE
# ============================================================


@app.route(
    "/record-sale",
    methods=["POST"]
)
def record_sale():

    customer_id = request.form.get(
        "customer_id"
    )

    payment_method = clean(
        request.form.get(
            "payment_method"
        )
    ) or "Cash"

    product_ids = request.form.getlist(
        "product_id[]"
    )

    quantities = request.form.getlist(
        "quantity[]"
    )

    if not product_ids:

        flash(
            "No products selected.",
            "error"
        )

        return redirect(
            url_for("sales")
        )

    sale_number = generate_number(
        "SALE"
    )

    sale = Sale(

        sale_number=sale_number,

        customer_id=(
            int(customer_id)
            if customer_id
            else None
        ),

        payment_method=payment_method,

        total_amount=Decimal("0.00"),

        total_cost=Decimal("0.00"),

        profit=Decimal("0.00")
    )

    db.session.add(sale)

    db.session.flush()

    total_amount = Decimal("0.00")

    total_cost = Decimal("0.00")

    total_profit = Decimal("0.00")

    try:

        for i, product_id in enumerate(
            product_ids
        ):

            product = Product.query.get(
                product_id
            )

            if not product:
                continue

            quantity = money(
                quantities[i]
                if i < len(quantities)
                else 0
            )

            if quantity <= 0:
                continue

            current_stock = money(
                product.stock_quantity
            )

            if quantity > current_stock:

                db.session.rollback()

                flash(
                    f"Not enough stock for "
                    f"{product.name}. "
                    f"Available: "
                    f"{current_stock:,.2f}.",
                    "error"
                )

                return redirect(
                    url_for("sales")
                )

            purchase_price = money(
                product.purchase_price
            )

            selling_price = money(
                product.selling_price
            )

            line_total = (
                quantity
                * selling_price
            )

            line_cost = (
                quantity
                * purchase_price
            )

            line_profit = (
                line_total
                - line_cost
            )

            item = SaleItem(

                sale_id=sale.id,

                product_id=product.id,

                quantity=quantity,

                purchase_price=purchase_price,

                selling_price=selling_price,

                total=line_total,

                cost=line_cost,

                profit=line_profit
            )

            db.session.add(item)

            # Automatically deduct stock.

            product.stock_quantity = (
                current_stock
                - quantity
            )

            movement = StockMovement(

                product_id=product.id,

                movement_type="SALE",

                quantity=-quantity,

                unit_cost=purchase_price,

                total_cost=-line_cost,

                reference=sale_number,

                notes=(
                    "Stock automatically deducted after sale."
                )
            )

            db.session.add(movement)

            total_amount += line_total

            total_cost += line_cost

            total_profit += line_profit

        if total_amount <= 0:

            db.session.rollback()

            flash(
                "Sale contains no valid items.",
                "error"
            )

            return redirect(
                url_for("sales")
            )

        sale.total_amount = total_amount

        sale.total_cost = total_cost

        sale.profit = total_profit

        db.session.commit()

    except Exception as error:

        db.session.rollback()

        print(
            "SALE ERROR:",
            error
        )

        flash(
            "Unable to record sale.",
            "error"
        )

        return redirect(
            url_for("sales")
        )

    flash(
        f"Sale {sale_number} recorded successfully. "
        f"Stock, cost and profit updated.",
        "success"
    )

    return redirect(
        url_for("sales")
    )


# ============================================================
# LOW STOCK
# ============================================================


@app.route("/low-stock")
def low_stock():

    products = Product.query.all()

    low_stock_products = [

        p
        for p in products

        if money(
            p.stock_quantity
        )
        <= money(
            p.minimum_stock
        )

    ]

    return render_template(
        "low_stock.html",
        products=low_stock_products
    )


# ============================================================
# REORDER LIST
# ============================================================


@app.route("/reorder-list")
def reorder_list():

    products = Product.query.all()

    reorder_products = []

    for product in products:

        current = money(
            product.stock_quantity
        )

        minimum = money(
            product.minimum_stock
        )

        if current <= minimum:

            recommended = max(
                minimum * 2 - current,
                Decimal("1")
            )

            reorder_products.append({

                "product": product,

                "current": current,

                "minimum": minimum,

                "recommended": recommended

            })

    return render_template(
        "reorder_list.html",
        products=reorder_products
    )


# ============================================================
# QUOTATIONS
# ============================================================


@app.route("/quotations")
def quotations():

    quotations = Quotation.query.order_by(
        Quotation.created_at.desc()
    ).all()

    customers = Customer.query.order_by(
        Customer.name.asc()
    ).all()

    products = Product.query.order_by(
        Product.name.asc()
    ).all()

    quotation_number = generate_number(
        "DAV"
    )

    return render_template(
        "quotations.html",
        quotations=quotations,
        customers=customers,
        products=products,
        quotation_number=quotation_number
    )


# ============================================================
# CREATE QUOTATION
# ============================================================


@app.route(
    "/create-quotation",
    methods=["POST"]
)
def create_quotation():

    customer_id = request.form.get(
        "customer_id"
    )

    customer_name = clean(
        request.form.get(
            "customer_name"
        )
    )

    customer_phone = clean(
        request.form.get(
            "customer_phone"
        )
    )

    customer_email = clean(
        request.form.get(
            "customer_email"
        )
    )

    project_type = clean(
        request.form.get(
            "project_type"
        )
    )

    project_location = clean(
        request.form.get(
            "project_location"
        )
    )

    validity = clean(
        request.form.get(
            "validity"
        )
    ) or "30 Days"

    notes = clean(
        request.form.get(
            "notes"
        )
    )

    terms = clean(
        request.form.get(
            "terms"
        )
    )

    # --------------------------------------------------------
    # AUTOMATIC CUSTOMER CREATION
    # --------------------------------------------------------

    customer = None

    if not customer_id and customer_name:

        customer = Customer(

            name=customer_name,

            phone=customer_phone,

            email=customer_email
        )

        db.session.add(customer)

        db.session.flush()

        customer_id = customer.id

    elif customer_id:

        customer = Customer.query.get(
            int(customer_id)
        )

    # --------------------------------------------------------
    # ITEMS
    # --------------------------------------------------------

    names = request.form.getlist(
        "item_name[]"
    )

    quantities = request.form.getlist(
        "quantity[]"
    )

    selling_prices = request.form.getlist(
        "unit_price[]"
    )

    purchase_prices = request.form.getlist(
        "purchase_price[]"
    )

    quotation_items = []

    subtotal = Decimal("0.00")

    total_cost = Decimal("0.00")

    max_items = max(
        len(names),
        len(quantities),
        len(selling_prices),
        len(purchase_prices)
    )

    for i in range(max_items):

        name = clean(
            names[i]
            if i < len(names)
            else ""
        )

        if not name:
            continue

        quantity = money(
            quantities[i]
            if i < len(quantities)
            else 0
        )

        unit_price = money(
            selling_prices[i]
            if i < len(selling_prices)
            else 0
        )

        purchase_price = money(
            purchase_prices[i]
            if i < len(purchase_prices)
            else 0
        )

        total = (
            quantity
            * unit_price
        )

        cost = (
            quantity
            * purchase_price
        )

        profit = (
            total
            - cost
        )

        quotation_items.append({

            "name": name,

            "quantity": quantity,

            "unit_price": unit_price,

            "purchase_price": purchase_price,

            "total": total,

            "cost": cost,

            "profit": profit
        })

        subtotal += total

        total_cost += cost

    if not quotation_items:

        db.session.rollback()

        flash(
            "Please add at least one quotation item.",
            "error"
        )

        return redirect(
            url_for("quotations")
        )

    quotation_number = generate_number(
        "DAV"
    )

    quotation = Quotation(

        quotation_number=quotation_number,

        customer_id=(
            customer.id
            if customer
            else None
        ),

        project_type=project_type,

        project_location=project_location,

        subtotal=subtotal,

        total_cost=total_cost,

        estimated_profit=(
            subtotal
            - total_cost
        ),

        validity=validity,

        notes=notes,

        terms=terms
    )

    db.session.add(quotation)

    db.session.flush()

    for item in quotation_items:

        quotation_item = QuotationItem(

            quotation_id=quotation.id,

            product_name=item["name"],

            quantity=item["quantity"],

            purchase_price=item[
                "purchase_price"
            ],

            unit_price=item[
                "unit_price"
            ],

            total=item["total"],

            cost=item["cost"],

            profit=item["profit"]
        )

        db.session.add(
            quotation_item
        )

    db.session.commit()

    flash(
        f"Quotation {quotation_number} created successfully.",
        "success"
    )

    return redirect(
        url_for(
            "quotation_pdf",
            quotation_id=quotation.id
        )
    )


# ============================================================
# QUOTATION PDF
# ============================================================


@app.route(
    "/quotation/<int:quotation_id>/pdf"
)
def quotation_pdf(quotation_id):

    quotation = Quotation.query.get_or_404(
        quotation_id
    )

    customer = quotation.customer

    pdf_buffer = BytesIO()

    document = SimpleDocTemplate(

        pdf_buffer,

        pagesize=A4,

        rightMargin=15 * mm,

        leftMargin=15 * mm,

        topMargin=14 * mm,

        bottomMargin=14 * mm,

        title=(
            f"Quotation "
            f"{quotation.quotation_number}"
        ),

        author=COMPANY_NAME
    )

    styles = getSampleStyleSheet()

    company_style = ParagraphStyle(

        "Company",

        parent=styles["Heading1"],

        fontName="Helvetica-Bold",

        fontSize=20,

        leading=23,

        textColor=colors.HexColor(
            "#062d4d"
        )
    )

    small_style = ParagraphStyle(

        "Small",

        parent=styles["Normal"],

        fontSize=8.5,

        leading=11,

        textColor=colors.HexColor(
            "#596a73"
        )
    )

    heading_style = ParagraphStyle(

        "Heading",

        parent=styles["Heading2"],

        fontName="Helvetica-Bold",

        fontSize=11,

        leading=14,

        textColor=colors.HexColor(
            "#062d4d"
        ),

        spaceAfter=7
    )

    right_style = ParagraphStyle(

        "Right",

        parent=small_style,

        alignment=TA_RIGHT
    )

    center_style = ParagraphStyle(

        "Center",

        parent=small_style,

        alignment=TA_CENTER
    )

    story = []

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    header = Table(

        [[

            Paragraph(
                COMPANY_NAME,
                company_style
            ),

            Paragraph(

                "<b>QUOTATION</b><br/><br/>"

                f"<b>No:</b> "
                f"{quotation.quotation_number}<br/>"

                f"<b>Date:</b> "
                f"{quotation.created_at.strftime('%d/%m/%Y')}<br/>"

                f"<b>Valid:</b> "
                f"{quotation.validity}",

                right_style
            )

        ]],

        colWidths=[
            105 * mm,
            65 * mm
        ]
    )

    header.setStyle(
        TableStyle([

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0
            )

        ])
    )

    story.append(header)

    story.append(
        Paragraph(
            COMPANY_TAGLINE,
            small_style
        )
    )

    story.append(
        Paragraph(

            f"{COMPANY_PHONE} | "
            f"{COMPANY_EMAIL} | "
            f"{COMPANY_LOCATION}",

            small_style
        )
    )

    story.append(
        Spacer(1, 6 * mm)
    )

    story.append(
        HRFlowable(

            width="100%",

            thickness=1.2,

            color=colors.HexColor(
                "#087f5b"
            )
        )
    )

    story.append(
        Spacer(1, 5 * mm)
    )

    # --------------------------------------------------------
    # CUSTOMER
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "CUSTOMER & PROJECT DETAILS",
            heading_style
        )
    )

    customer_name = (
        customer.name
        if customer
        else "Valued Customer"
    )

    customer_phone = (
        customer.phone
        if customer
        else "-"
    )

    customer_email = (
        customer.email
        if customer
        else "-"
    )

    customer_table = Table(

        [

            [

                Paragraph(

                    f"<b>Customer</b><br/>"
                    f"{customer_name}",

                    small_style
                ),

                Paragraph(

                    f"<b>Phone</b><br/>"
                    f"{customer_phone}",

                    small_style
                )

            ],

            [

                Paragraph(

                    f"<b>Email</b><br/>"
                    f"{customer_email}",

                    small_style
                ),

                Paragraph(

                    f"<b>Project</b><br/>"
                    f"{quotation.project_type or '-'}",

                    small_style
                )

            ],

            [

                Paragraph(

                    f"<b>Location</b><br/>"
                    f"{quotation.project_location or '-'}",

                    small_style
                ),

                Paragraph(

                    f"<b>Date</b><br/>"
                    f"{quotation.created_at.strftime('%d/%m/%Y')}",

                    small_style
                )

            ]

        ],

        colWidths=[
            85 * mm,
            85 * mm
        ]
    )

    customer_table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                colors.HexColor(
                    "#f3f7f8"
                )
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor(
                    "#d6e2e5"
                )
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                7
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                7
            )

        ])
    )

    story.append(
        customer_table
    )

    story.append(
        Spacer(1, 7 * mm)
    )

    # --------------------------------------------------------
    # ITEMS
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "QUOTATION ITEMS",
            heading_style
        )
    )

    table_data = [

        [

            Paragraph(
                "<b>#</b>",
                center_style
            ),

            Paragraph(
                "<b>Item / Description</b>",
                small_style
            ),

            Paragraph(
                "<b>Qty</b>",
                center_style
            ),

            Paragraph(
                "<b>Unit Price</b>",
                right_style
            ),

            Paragraph(
                "<b>Total</b>",
                right_style
            )

        ]

    ]

    for number, item in enumerate(
        quotation.items,
        start=1
    ):

        table_data.append([

            Paragraph(
                str(number),
                center_style
            ),

            Paragraph(
                item.product_name,
                small_style
            ),

            Paragraph(
                f"{money(item.quantity):,.2f}",
                center_style
            ),

            Paragraph(
                format_money(
                    item.unit_price
                ),
                right_style
            ),

            Paragraph(
                format_money(
                    item.total
                ),
                right_style
            )

        ])

    items_table = Table(

        table_data,

        colWidths=[

            10 * mm,

            72 * mm,

            20 * mm,

            35 * mm,

            35 * mm

        ],

        repeatRows=1
    )

    items_table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor(
                    "#062d4d"
                )
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.45,
                colors.HexColor(
                    "#d5dfe2"
                )
            ),

            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor(
                        "#f8fafb"
                    )
                ]
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                6
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                6
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                7
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                7
            )

        ])
    )

    story.append(
        items_table
    )

    story.append(
        Spacer(1, 5 * mm)
    )

    # --------------------------------------------------------
    # TOTALS
    # --------------------------------------------------------

    totals = Table(

        [

            [

                Paragraph(
                    "<b>SUBTOTAL</b>",
                    right_style
                ),

                Paragraph(

                    f"<b>"
                    f"{format_money(quotation.subtotal)}"
                    f"</b>",

                    right_style
                )

            ],

            [

                Paragraph(
                    "<b>TOTAL QUOTATION</b>",
                    right_style
                ),

                Paragraph(

                    f"<b>"
                    f"{format_money(quotation.subtotal)}"
                    f"</b>",

                    right_style
                )

            ]

        ],

        colWidths=[
            135 * mm,
            37 * mm
        ]
    )

    totals.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 1),
                (-1, 1),
                colors.HexColor(
                    "#eaf7f2"
                )
            ),

            (
                "BOX",
                (0, 1),
                (-1, 1),
                0.7,
                colors.HexColor(
                    "#087f5b"
                )
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                7
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                7
            )

        ])
    )

    story.append(
        totals
    )

    story.append(
        Spacer(1, 7 * mm)
    )

    # --------------------------------------------------------
    # NOTES
    # --------------------------------------------------------

    if quotation.notes:

        story.append(
            Paragraph(
                "NOTES",
                heading_style
            )
        )

        story.append(
            Paragraph(

                quotation.notes.replace(
                    "\n",
                    "<br/>"
                ),

                small_style
            )
        )

        story.append(
            Spacer(1, 5 * mm)
        )

    # --------------------------------------------------------
    # TERMS
    # --------------------------------------------------------

    if quotation.terms:

        story.append(
            Paragraph(
                "TERMS & CONDITIONS",
                heading_style
            )
        )

        story.append(
            Paragraph(

                quotation.terms.replace(
                    "\n",
                    "<br/>"
                ),

                small_style
            )
        )

        story.append(
            Spacer(1, 7 * mm)
        )

    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    story.append(
        HRFlowable(

            width="100%",

            thickness=0.7,

            color=colors.HexColor(
                "#d4dfe2"
            )
        )
    )

    story.append(
        Spacer(1, 4 * mm)
    )

    story.append(
        Paragraph(

            f"<b>{COMPANY_NAME}</b><br/>"
            f"{COMPANY_TAGLINE}<br/>"
            f"Phone: {COMPANY_PHONE} | "
            f"Email: {COMPANY_EMAIL}<br/>"
            f"{COMPANY_LOCATION}",

            center_style
        )
    )

    document.build(
        story
    )

    pdf_buffer.seek(0)

    filename = (
        f"Davanso_Quotation_"
        f"{quotation.quotation_number}.pdf"
    )

    return send_file(

        pdf_buffer,

        as_attachment=True,

        download_name=filename,

        mimetype="application/pdf"
    )


# ============================================================
# REPORTS
# ============================================================


@app.route("/reports")
def reports():

    all_sales = Sale.query.all()

    all_expenses = Expense.query.all()

    # --------------------------------------------------------
    # TODAY
    # --------------------------------------------------------

    today_sales = [

        sale

        for sale in all_sales

        if sale.created_at
        and sale.created_at.date()
        == today()

    ]

    today_expenses = [

        expense

        for expense in all_expenses

        if expense.created_at
        and expense.created_at.date()
        == today()

    ]

    daily_sales = sum(
        (
            money(s.total_amount)
            for s in today_sales
        ),
        Decimal("0.00")
    )

    daily_cost = sum(
        (
            money(s.total_cost)
            for s in today_sales
        ),
        Decimal("0.00")
    )

    daily_profit = sum(
        (
            money(s.profit)
            for s in today_sales
        ),
        Decimal("0.00")
    )

    daily_expenses = sum(
        (
            money(e.amount)
            for e in today_expenses
        ),
        Decimal("0.00")
    )

    # --------------------------------------------------------
    # MONTH
    # --------------------------------------------------------

    current_month = today().month

    current_year = today().year

    monthly_sales_records = [

        sale

        for sale in all_sales

        if sale.created_at

        and sale.created_at.month
        == current_month

        and sale.created_at.year
        == current_year

    ]

    monthly_expense_records = [

        expense

        for expense in all_expenses

        if expense.created_at

        and expense.created_at.month
        == current_month

        and expense.created_at.year
        == current_year

    ]

    monthly_sales = sum(
        (
            money(s.total_amount)
            for s in monthly_sales_records
        ),
        Decimal("0.00")
    )

    monthly_cost = sum(
        (
            money(s.total_cost)
            for s in monthly_sales_records
        ),
        Decimal("0.00")
    )

    monthly_profit = sum(
        (
            money(s.profit)
            for s in monthly_sales_records
        ),
        Decimal("0.00")
    )

    monthly_expenses = sum(
        (
            money(e.amount)
            for e in monthly_expense_records
        ),
        Decimal("0.00")
    )

    # --------------------------------------------------------
    # STOCK
    # --------------------------------------------------------

    products = Product.query.all()

    total_stock_units = sum(
        (
            money(p.stock_quantity)
            for p in products
        ),
        Decimal("0.00")
    )

    stock_value = sum(
        (
            money(p.stock_quantity)
            * money(p.purchase_price)
            for p in products
        ),
        Decimal("0.00")
    )

    low_stock = [

        p

        for p in products

        if money(
            p.stock_quantity
        )
        <= money(
            p.minimum_stock
        )

    ]

    return render_template(

        "reports.html",

        daily_sales=daily_sales,

        daily_cost=daily_cost,

        daily_profit=daily_profit,

        daily_expenses=daily_expenses,

        monthly_sales=monthly_sales,

        monthly_cost=monthly_cost,

        monthly_profit=monthly_profit,

        monthly_expenses=monthly_expenses,

        total_stock_units=total_stock_units,

        stock_value=stock_value,

        low_stock=low_stock

    )


# ============================================================
# ADD EXPENSE
# ============================================================


@app.route(
    "/add-expense",
    methods=["POST"]
)
def add_expense():

    description = clean(
        request.form.get(
            "description"
        )
    )

    amount = money(
        request.form.get(
            "amount"
        )
    )

    category = clean(
        request.form.get(
            "category"
        )
    )

    if not description:

        flash(
            "Expense description is required.",
            "error"
        )

        return redirect(
            url_for("reports")
        )

    if amount <= 0:

        flash(
            "Expense amount must be greater than zero.",
            "error"
        )

        return redirect(
            url_for("reports")
        )

    expense = Expense(

        description=description,

        amount=amount,

        category=category
    )

    db.session.add(
        expense
    )

    db.session.commit()

    flash(
        "Expense recorded successfully.",
        "success"
    )

    return redirect(
        url_for("reports")
    )


# ============================================================
# SALES SUMMARY API
# ============================================================


@app.route(
    "/api/sales-summary"
)
def sales_summary_api():

    sales = Sale.query.all()

    total_sales = sum(
        (
            money(s.total_amount)
            for s in sales
        ),
        Decimal("0.00")
    )

    total_cost = sum(
        (
            money(s.total_cost)
            for s in sales
        ),
        Decimal("0.00")
    )

    total_profit = sum(
        (
            money(s.profit)
            for s in sales
        ),
        Decimal("0.00")
    )

    return jsonify({

        "total_sales": float(
            total_sales
        ),

        "total_cost": float(
            total_cost
        ),

        "total_profit": float(
            total_profit
        ),

        "number_of_sales": len(
            sales
        )

    })


# ============================================================
# INVENTORY API
# ============================================================


@app.route(
    "/api/inventory"
)
def inventory_api():

    products = Product.query.all()

    return jsonify([

        {

            "id": product.id,

            "name": product.name,

            "category": product.category,

            "purchase_price": float(
                money(
                    product.purchase_price
                )
            ),

            "selling_price": float(
                money(
                    product.selling_price
                )
            ),

            "stock": float(
                money(
                    product.stock_quantity
                )
            ),

            "minimum_stock": float(
                money(
                    product.minimum_stock
                )
            ),

            "low_stock": (
                money(
                    product.stock_quantity
                )
                <=
                money(
                    product.minimum_stock
                )
            )

        }

        for product in products

    ])


# ============================================================
# CONTACT FORM
# ============================================================


@app.route(
    "/submit-contact",
    methods=["POST"]
)
def submit_contact():

    name = clean(
        request.form.get("name")
    )

    phone = clean(
        request.form.get("phone")
    )

    email = clean(
        request.form.get("email")
    )

    location = clean(
        request.form.get("location")
    )

    service = clean(
        request.form.get("service")
    )

    message = clean(
        request.form.get("message")
    )

    print()
    print("=" * 70)
    print(
        "NEW DAVANSO SOLUTIONS CONTACT MESSAGE"
    )
    print("=" * 70)

    print("Name:", name)
    print("Phone:", phone)
    print("Email:", email)
    print("Location:", location)
    print("Service:", service)
    print("Message:", message)

    print("=" * 70)

    flash(
        "Thank you. Your message has been received.",
        "success"
    )

    return redirect(
        url_for("contact")
    )


# ============================================================
# TEST PDF
# ============================================================


@app.route("/test-pdf")
def test_pdf():

    buffer = BytesIO()

    document = SimpleDocTemplate(

        buffer,

        pagesize=A4,

        rightMargin=20 * mm,

        leftMargin=20 * mm,

        topMargin=20 * mm,

        bottomMargin=20 * mm
    )

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            COMPANY_NAME,
            styles["Title"]
        )
    )

    story.append(
        Spacer(1, 10)
    )

    story.append(
        Paragraph(
            "PDF generation is working correctly.",
            styles["Normal"]
        )
    )

    story.append(
        Spacer(1, 10)
    )

    story.append(
        Paragraph(

            f"Generated on "
            f"{datetime.now().strftime('%d/%m/%Y %H:%M')}",

            styles["Normal"]
        )
    )

    document.build(
        story
    )

    buffer.seek(0)

    return send_file(

        buffer,

        as_attachment=True,

        download_name="Davanso_Test.pdf",

        mimetype="application/pdf"
    )


# ============================================================
# 404 ERROR
# ============================================================


@app.errorhandler(404)
def page_not_found(error):

    return """

    <!DOCTYPE html>

    <html>

    <head>

        <title>Page Not Found</title>

        <meta
            name="viewport"
            content="width=device-width, initial-scale=1"
        >

        <style>

            body {
                font-family: Arial, sans-serif;
                background: #f4f7f8;
                text-align: center;
                padding: 70px;
            }

            h1 {
                color: #062d4d;
                font-size: 60px;
            }

            p {
                color: #667;
            }

            a {
                display: inline-block;
                margin-top: 20px;
                padding: 12px 22px;
                background: #087f5b;
                color: white;
                text-decoration: none;
                border-radius: 6px;
            }

        </style>

    </head>

    <body>

        <h1>404</h1>

        <h2>Page Not Found</h2>

        <p>
            The page you are looking for does not exist.
        </p>

        <a href="/">
            Return Home
        </a>

    </body>

    </html>

    """, 404


# ============================================================
# GENERAL ERROR HANDLER
# ============================================================


@app.errorhandler(500)
def internal_error(error):

    try:
        db.session.rollback()
    except Exception:
        pass

    return """

    <!DOCTYPE html>

    <html>

    <head>

        <title>Server Error</title>

        <meta
            name="viewport"
            content="width=device-width, initial-scale=1"
        >

        <style>

            body {
                font-family: Arial, sans-serif;
                background: #f4f7f8;
                text-align: center;
                padding: 70px;
            }

            h1 {
                color: #062d4d;
                font-size: 50px;
            }

            p {
                color: #667;
            }

            a {
                display: inline-block;
                margin-top: 20px;
                padding: 12px 22px;
                background: #087f5b;
                color: white;
                text-decoration: none;
                border-radius: 6px;
            }

        </style>

    </head>

    <body>

        <h1>500</h1>

        <h2>Something Went Wrong</h2>

        <p>
            The system encountered an unexpected error.
        </p>

        <a href="/">
            Return Home
        </a>

    </body>

    </html>

    """, 500


# ============================================================
# APPLICATION START
# ============================================================


if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    print()
    print("=" * 70)
    print("DAVANSO SOLUTIONS LTD")
    print("AUTOMATED BUSINESS MANAGEMENT SYSTEM")
    print("=" * 70)
    print()
    print(
        f"Running on port {port}"
    )
    print()
    print("=" * 70)

    app.run(

        host="0.0.0.0",

        port=port,

        debug=False

    )