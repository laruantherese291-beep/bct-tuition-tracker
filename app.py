from datetime import datetime
import json
import os
import re
import flet as ft

SEMESTER_CONFIGS = {
    "1st Semester": {
        "tuition_per_unit": 459.54,
        "misc_fee": 3739.98,
        "lab_fee_per_subject": 2341.86,
        "hands_on_fee_per_subject": 2341.86,
    },
    "2nd Semester": {
        "tuition_per_unit": 459.54,
        "misc_fee": 3739.98,
        "lab_fee_per_subject": 2341.86,
        "hands_on_fee_per_subject": 2341.86,
    }
}

DOWN_PAYMENT_MIN = 3500
MAX_UNITS = 25.0

DB_FILE = os.path.join(
    os.getenv("FLET_APP_STORAGE_DATA", "."),
    "student_records.json",
)
PAYMENT_SCHEDULE = [
    ("1st Prelim", 15),
    ("1st Grading", 25),
    ("2nd Prelim", 15),
    ("Mid Term", 30),
    ("Finals", 15),
]

assert sum(pct for _, pct in PAYMENT_SCHEDULE) == 100, "PAYMENT_SCHEDULE percentages must add up to 100."

PRIMARY, GOLD, BG, WHITE = "#800000", "#D4AF37", "#FDFBFB", "#FFFFFF"
TEXT, MUTED, LINE, ERROR = "#4A0E0E", "#7A5C5C", "#EEDDDD", "#C0392B"


def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_db(data):
    try:
        with open(DB_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass


def parse_decimal_number(text, minimum, maximum, name):
    """Return (value, error). Accepts integers and decimals."""
    t = (text or "").strip()
    if not t:
        return None, f"{name} cannot be empty."
    if not re.fullmatch(r"[0-9]+(\.[0-9]+)?", t):
        return None, f"{name} must be a valid number."
    n = float(t)
    if n < minimum or n > maximum:
        return None, f"{name} must be from {minimum} to {maximum}."
    return n, None


def parse_whole_number(text, minimum, maximum, name):
    """Return (value, error). Accepts only plain digits 0-9."""
    t = (text or "").strip()
    if not t:
        return None, f"{name} cannot be empty."
    if not re.fullmatch(r"[0-9]+", t):
        return None, f"{name} must be a whole number."
    n = int(t)
    if n < minimum or n > maximum:
        return None, f"{name} must be from {minimum} to {maximum}."
    return n, None


def compute_assessment(semester, units, lab_subjects, hands_on_subjects):
    cfg = SEMESTER_CONFIGS.get(semester, SEMESTER_CONFIGS["1st Semester"])
    tuition = cfg["tuition_per_unit"] * units
    lab_fee = cfg["lab_fee_per_subject"] * lab_subjects
    hands_on_fee = cfg["hands_on_fee_per_subject"] * hands_on_subjects
    total = tuition + cfg["misc_fee"] + lab_fee + hands_on_fee
    return tuition, cfg["misc_fee"], lab_fee, hands_on_fee, total


def compute_payment_breakdown(total):
    total_c = int(round(total * 100))
    down_c = min(total_c, DOWN_PAYMENT_MIN * 100)
    remainder_c = total_c - down_c
    amounts_c, used = [], 0
    for i, (_, pct) in enumerate(PAYMENT_SCHEDULE):
        if i == len(PAYMENT_SCHEDULE) - 1:
            amount = remainder_c - used
        else:
            amount = (remainder_c * pct + 50) // 100
        amounts_c.append(amount)
        used += amount
    payments = [(name, pct, c / 100) for (name, pct), c in zip(PAYMENT_SCHEDULE, amounts_c)]
    return down_c / 100, remainder_c / 100, payments


def money(n):
    return f"Php {n:,.2f}"


def border_all(width, color):
    """Version-safe border helper for Flet."""
    if hasattr(ft, "border") and hasattr(ft.border, "all"):
        return ft.border.all(width, color)
    if hasattr(ft, "Border") and hasattr(ft.Border, "all"):
        return ft.Border.all(width, color)
    return ft.border.all(width, color)


def main(page: ft.Page):
    page.title = "TUITION TRACKER"
    page.window.icon = "icon.png"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(
        color_scheme_seed=PRIMARY,
        use_material3=True,
    )
    page.bgcolor = BG
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO

    err_attr = "error" if hasattr(ft.TextField, "error") else "error_text"

    def set_error(field, message):
        setattr(field, err_attr, message)

    def card(*controls, bgcolor=WHITE):
        return ft.Container(
            content=ft.Column(
                controls=list(controls),
                spacing=12,
                tight=True,
            ),
            bgcolor=bgcolor,
            border=border_all(1, LINE),
            border_radius=18,
            padding=20,
            width=float("inf"),
        )

    def line(label, amount, note=None, bold=False):
        left = [ft.Text(
            label,
            weight=ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL,
            color=TEXT,
        )]
        if note:
            left.append(ft.Text(note, size=12, color=MUTED))

        return ft.Row(
            [
                ft.Column(left, spacing=3, expand=True),
                ft.Text(
                    amount,
                    color=TEXT,
                    weight=ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL,
                    text_align=ft.TextAlign.RIGHT,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    page.appbar = ft.AppBar(
        leading=ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED),
        title=ft.Text("TUITION TRACKER", weight=ft.FontWeight.BOLD),
        center_title=False,
        bgcolor=PRIMARY,
        color=WHITE,
    )

    student_id_field = ft.TextField(
        label="Student ID Number",
        border=ft.OutlineInputBorder(border_radius=12),
        filled=True,
        fill_color=WHITE,
    )
    student_name_field = ft.TextField(
        label="Full Name",
        border=ft.OutlineInputBorder(border_radius=12),
        filled=True,
        fill_color=WHITE,
    )
    course_field = ft.TextField(
        label="Course / Program",
        border=ft.OutlineInputBorder(border_radius=12),
        filled=True,
        fill_color=WHITE,
    )
    year_level_field = ft.Dropdown(
        label="Year Level",
        border=ft.OutlineInputBorder(border_radius=12),
        filled=True,
        fill_color=WHITE,
        options=[
            ft.dropdown.Option("1st Year"),
            ft.dropdown.Option("2nd Year"),
            ft.dropdown.Option("3rd Year"),
            ft.dropdown.Option("4th Year"),
        ],
    )
    semester_field = ft.Dropdown(
        label="Semester",
        value="1st Semester",
        border=ft.OutlineInputBorder(border_radius=12),
        filled=True,
        fill_color=WHITE,
        options=[
            ft.dropdown.Option("1st Semester"),
            ft.dropdown.Option("2nd Semester"),
        ],
    )

    def make_field(label, value="0", expand=False):
        return ft.TextField(
            label=label,
            value=value,
            keyboard_type=ft.KeyboardType.NUMBER,
            border=ft.OutlineInputBorder(border_radius=12),
            filled=True,
            fill_color=WHITE,
            expand=expand,
        )

    units = make_field("Total units (1-25)", "")
    lab = make_field("Lab subjects", "0", expand=True)
    hands_on = make_field("Hands-on subjects", "0", expand=True)

    result_data = None
    total_paid = 0.0
    payment_history = []
    past_records = []

    payment_input_field = ft.TextField(
        label="Enter payment amount (₱)",
        keyboard_type=ft.KeyboardType.NUMBER,
        border=ft.OutlineInputBorder(border_radius=12),
        filled=True,
        fill_color=WHITE,
    )

    selected_tab = 0
    screen_area = ft.Column(
        spacing=16,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    def on_student_id_blur(e):
        nonlocal total_paid, payment_history, past_records, result_data
        sid = (student_id_field.value or "").strip()
        if not sid:
            return
        db = load_db()
        if sid in db:
            record = db[sid]
            student_name_field.value = record.get("name", "")
            course_field.value = record.get("course", "")
            year_level_field.value = record.get("year_level", "1st Year")
            semester_field.value = record.get("semester", "1st Semester")
            units.value = str(record.get("units", ""))
            lab.value = str(record.get("lab", "0"))
            hands_on.value = str(record.get("hands_on", "0"))
            total_paid = record.get("total_paid", 0.0)
            payment_history = record.get("payment_history", [])
            past_records = record.get("past_records", [])

            u = record.get("units")
            n_lab = record.get("lab", 0)
            n_ho = record.get("hands_on", 0)
            sem = semester_field.value
            if u is not None:
                tuition, misc, lab_fee, ho_fee, total = compute_assessment(sem, u, n_lab, n_ho)
                result_data = (sid, student_name_field.value, course_field.value, year_level_field.value, sem, u, n_lab,
                               n_ho, tuition, misc, lab_fee, ho_fee, total)
            page.update()

    student_id_field.on_blur = on_student_id_blur

    def validate():
        for field in (student_id_field, student_name_field, course_field, year_level_field, semester_field, units, lab,
                      hands_on):
            set_error(field, None)

        has_error = False
        if not (student_id_field.value or "").strip():
            set_error(student_id_field, "Student ID is required.")
            has_error = True
        if not (student_name_field.value or "").strip():
            set_error(student_name_field, "Name is required.")
            has_error = True
        if not (course_field.value or "").strip():
            set_error(course_field, "Course is required.")
            has_error = True
        if not (year_level_field.value or "").strip():
            set_error(year_level_field, "Year level is required.")
            has_error = True
        if not (semester_field.value or "").strip():
            set_error(semester_field, "Semester is required.")
            has_error = True

        u, err = parse_decimal_number(units.value, 1.0, float(MAX_UNITS), "Units")
        if err:
            set_error(units, err)
            has_error = True

        cap = int(u) if u is not None else int(MAX_UNITS)
        counts = []
        for field, name in ((lab, "Lab subjects"), (hands_on, "Hands-on subjects")):
            n, err = parse_whole_number(
                (field.value or "").strip() or "0", 0, cap, name
            )
            if err:
                set_error(field, err)
                has_error = True
            counts.append(n)

        if has_error or u is None or any(n is None for n in counts):
            return None

        return student_id_field.value.strip(), student_name_field.value.strip(), course_field.value.strip(), year_level_field.value.strip(), semester_field.value.strip(), u, \
        counts[0], counts[1]

    def on_units_change(e):
        nonlocal result_data
        u_val, err = parse_decimal_number(units.value, 1.0, float(MAX_UNITS), "Units")
        if err:
            set_error(units, err if (units.value or "").strip() else None)
            result_data = None
        else:
            set_error(units, None)
            sem = semester_field.value or "1st Semester"
            try:
                n_lab = int(lab.value or "0")
            except ValueError:
                n_lab = 0
            try:
                n_ho = int(hands_on.value or "0")
            except ValueError:
                n_ho = 0
            tuition, misc, lab_fee, ho_fee, total = compute_assessment(sem, u_val, n_lab, n_ho)
            sid = (student_id_field.value or "").strip() or "DRAFT"
            sname = (student_name_field.value or "").strip() or "Student"
            scourse = (course_field.value or "").strip() or "Course"
            syear = year_level_field.value or "1st Year"
            result_data = (sid, sname, scourse, syear, sem, u_val, n_lab, n_ho, tuition, misc, lab_fee, ho_fee, total)
        page.update()

    units.on_change = on_units_change

    def enrollment_screen():
        def stepper(field, label, fee):
            def change(delta):
                n, _ = parse_whole_number(field.value or "0", 0, int(MAX_UNITS), "Subjects")
                current = n if n is not None else 0
                u_val, _ = parse_decimal_number(units.value, 1.0, float(MAX_UNITS), "Units")
                cap = int(u_val) if u_val is not None else int(MAX_UNITS)
                field.value = str(max(0, min(cap, current + delta)))
                set_error(field, None)
                on_units_change(None)

            return ft.Column(
                [
                    ft.Text(label, color=TEXT, size=13),
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.Icons.REMOVE_CIRCLE_OUTLINE,
                                on_click=lambda e: change(-1),
                            ),
                            ft.Container(content=field, expand=True),
                            ft.IconButton(
                                icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                                on_click=lambda e: change(1),
                            ),
                        ],
                        spacing=4,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Text("Subject fee applies", size=12, color=MUTED),
                ],
                spacing=3,
            )

        return [
            ft.Container(
                content=ft.Row(
                    [
                        ft.Image(
    src="icon.png",
    width=48,
    height=48,
    fit="contain",
),
                        ft.Column(
                            [
                                ft.Text("Tuition Payment Tracker", size=22, weight=ft.FontWeight.BOLD, color=WHITE),
                                ft.Text(
                                    "Please settle your tuition fees on time to avoid delays in your enrollment. Thank you!",
                                    size=13, color="#F5E6E6"
                                ),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=14,
                ),
                bgcolor=PRIMARY,
                border_radius=22,
                padding=22,
            ),
            card(
                ft.Text("Student Information", size=19, weight=ft.FontWeight.BOLD, color=PRIMARY),
                student_id_field,
                student_name_field,
                course_field,
                year_level_field,
                semester_field,
            ),
            card(
                ft.Text("Fee Estimation", size=19, weight=ft.FontWeight.BOLD, color=PRIMARY),
                ft.Text(
                    "Add your units and subject types below. Computations update live as you type.",
                    size=13, color=MUTED),
                units,
                stepper(lab, "Subjects with laboratory", 3000),
                stepper(hands_on, "Hands-on subjects", 800),
                ft.Button(
                    content=ft.Text("Save"),
                    icon=ft.Icons.CALCULATE,
                    on_click=lambda e: compute(),
                    style=ft.ButtonStyle(
                        bgcolor=PRIMARY,
                        color=WHITE,
                        shape=ft.RoundedRectangleBorder(radius=14),
                        padding=18,
                    ),
                    width=float("inf"),
                ),
                ft.OutlinedButton(
                    "Reset",
                    icon=ft.Icons.REFRESH,
                    on_click=lambda e: reset(),
                    width=float("inf"),
                ),
            ),
        ]

    def assessment_screen():
        if result_data is None:
            return [empty_state(
                "No assessment yet",
                "Enter valid unit details above, then tap Save.",
                ft.Icons.RECEIPT_LONG,
            )]

        sid, sname, scourse, syear, ssem, u, n_lab, n_ho, tuition, misc, lab_fee, ho_fee, total = result_data
        cfg = SEMESTER_CONFIGS.get(ssem, SEMESTER_CONFIGS["1st Semester"])

        return [
            ft.Text("Your assessment", size=25, weight=ft.FontWeight.BOLD, color=PRIMARY),
            ft.Text(f"Student: {sname} ({sid}) | {syear} - {ssem} | {scourse}", color=MUTED),
            card(
                ft.Text("ESTIMATED SEMESTER TOTAL", size=12, color="#F5E6E6", weight=ft.FontWeight.BOLD),
                ft.Text(money(total), size=30, color=WHITE, weight=ft.FontWeight.BOLD),
                bgcolor=PRIMARY,
            ),
            card(
                line("Tuition fee", money(tuition), f"{cfg['tuition_per_unit']:,} × {u} units"),
                line("Miscellaneous fee", money(misc)),
                line("Laboratory fee", money(lab_fee), f"{n_lab} × {cfg['lab_fee_per_subject']:,}"),
                line("Hands-on fee", money(ho_fee), f"{n_ho} × {cfg['hands_on_fee_per_subject']:,}"),
                ft.Divider(color=LINE),
                line("Total assessment", money(total), bold=True),
            ),
            ft.FilledButton(
                "View payment",
                icon=ft.Icons.PAYMENTS,
                on_click=lambda e: navigate(2),
                width=float("inf"),
                style=ft.ButtonStyle(bgcolor=PRIMARY, color=WHITE, padding=16),
            ),
        ]

    def payment_screen():
        nonlocal total_paid
        if result_data is None:
            return [empty_state(
                "No payment breakdown yet",
                "Calculate your assessment first to see the payment schedule.",
                ft.Icons.ACCOUNT_BALANCE_WALLET,
            )]

        sid, sname, scourse, syear, ssem, *_, total = result_data
        down, remainder, payments = compute_payment_breakdown(total)

        current_balance = max(0.0, total - total_paid)

        def make_payment(e):
            nonlocal total_paid
            try:
                amt = float(payment_input_field.value or "0")
                if amt <= 0:
                    return
                total_paid += amt

                now_str = datetime.now().strftime("%B %d, %Y - %I:%M:%S %p")
                payment_history.append({"amount": amt, "timestamp": now_str})

                db = load_db()
                if sid in db and sid != "DRAFT":
                    db[sid]["total_paid"] = total_paid
                    db[sid]["payment_history"] = payment_history
                    save_db(db)

                payment_input_field.value = ""
                render_screen()
            except ValueError:
                pass

        rows = [
            ft.Text("Your payment plan", size=25, weight=ft.FontWeight.BOLD, color=PRIMARY),
            ft.Text(f"Student: {sname} ({sid}) | {syear} - {ssem} | {scourse}", color=MUTED),
            card(
                line("Total assessment", money(total), bold=True),
                line("Total paid", money(total_paid)),
                line("Remaining balance", money(current_balance), bold=True, note="Updated balance left"),
            ),
            card(
                ft.Text("Make a Payment", size=18, weight=ft.FontWeight.BOLD, color=PRIMARY),
                payment_input_field,
                ft.FilledButton(
                    "Submit Payment",
                    icon=ft.Icons.CHECK,
                    on_click=make_payment,
                    style=ft.ButtonStyle(bgcolor=PRIMARY, color=WHITE),
                    width=float("inf"),
                )
            )
        ]

        if payment_history:
            history_items = [
                ft.Text("Current Semester Payment History", size=18, weight=ft.FontWeight.BOLD, color=PRIMARY)
            ]
            for idx, item in enumerate(payment_history, 1):
                history_items.append(
                    line(f"Payment #{idx}", money(item["amount"]), note=item["timestamp"])
                )
            rows.append(card(*history_items))

        if past_records:
            past_items = [
                ft.Text("Past Semesters & Years Archive", size=18, weight=ft.FontWeight.BOLD, color=PRIMARY),
                ft.Text("Completed semester and year-level records.", size=12, color=MUTED)
            ]
            for pr in past_records:
                past_items.append(ft.Divider(color=LINE))
                past_items.append(line(f"{pr['year_level']} - {pr['semester']}", f"Total: {money(pr['total'])}",
                                       note=f"Course: {pr['course']} | Units: {pr['units']}"))
                past_items.append(line("Paid / Status", money(pr['total_paid']), note="Archived Record"))
            rows.append(card(*past_items))

        if current_balance > 0:
            rows.append(
                card(
                    ft.Text("Installment", size=18, weight=ft.FontWeight.BOLD, color=PRIMARY),
                    *[
                        line(name, money(amount), f"{pct}% of balance")
                        for name, pct, amount in payments
                    ],
                )
            )
        else:
            rows.append(
                card(ft.Text("Account is fully paid!", color=GOLD, weight=ft.FontWeight.BOLD))
            )

        return rows

    def empty_state(title, message, icon):
        return card(
            ft.Icon(icon, size=48, color=PRIMARY),
            ft.Text(title, size=19, weight=ft.FontWeight.BOLD, color=PRIMARY),
            ft.Text(message, color=MUTED),
            bgcolor=WHITE,
        )

    def render_screen():
        builders = [enrollment_screen, assessment_screen, payment_screen]
        screen_area.controls = builders[selected_tab]()
        page.update()

    def navigate(index):
        nonlocal selected_tab
        selected_tab = index
        page.navigation_bar.selected_index = index
        render_screen()

    page.navigation_bar = ft.NavigationBar(
        selected_index=0,
        on_change=lambda e: navigate(e.control.selected_index),
        bgcolor=WHITE,
        indicator_color="#F2D6D6",
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.EDIT_NOTE, label="Details"),
            ft.NavigationBarDestination(icon=ft.Icons.RECEIPT_LONG, label="Assessment"),
            ft.NavigationBarDestination(icon=ft.Icons.PAYMENTS, label="Pay plan"),
        ],
    )

    def compute():
        nonlocal result_data, total_paid, payment_history, past_records
        values = validate()
        if values is None:
            page.update()
            return

        sid, sname, scourse, syear, ssem, u, n_lab, n_ho = values
        tuition, misc, lab_fee, ho_fee, total = compute_assessment(ssem, u, n_lab, n_ho)

        result_data = (sid, sname, scourse, syear, ssem, u, n_lab, n_ho, tuition, misc, lab_fee, ho_fee, total)

        db = load_db()
        if sid in db:
            old_record = db[sid]
            old_year = old_record.get("year_level", "1st Year")
            old_sem = old_record.get("semester", "1st Semester")
            past_records = old_record.get("past_records", [])

            if old_year != syear or old_sem != ssem:
                archive_entry = {
                    "year_level": old_year,
                    "semester": old_sem,
                    "course": old_record.get("course", scourse),
                    "units": old_record.get("units", u),
                    "total": old_record.get("total", total),
                    "total_paid": old_record.get("total_paid", 0.0),
                    "payment_history": old_record.get("payment_history", [])
                }
                if not any(p["year_level"] == old_year and p["semester"] == old_sem for p in past_records):
                    past_records.append(archive_entry)

                total_paid = 0.0
                payment_history = []
            else:
                total_paid = old_record.get("total_paid", 0.0)
                payment_history = old_record.get("payment_history", [])
        else:
            total_paid = 0.0
            payment_history = []
            past_records = []

        db[sid] = {
            "name": sname,
            "course": scourse,
            "year_level": syear,
            "semester": ssem,
            "units": u,
            "lab": n_lab,
            "hands_on": n_ho,
            "total": total,
            "total_paid": total_paid,
            "payment_history": payment_history,
            "past_records": past_records
        }
        save_db(db)

        navigate(1)

    def reset():
        nonlocal result_data, total_paid, payment_history, past_records
        result_data = None
        total_paid = 0.0
        payment_history = []
        past_records = []
        student_id_field.value = ""
        student_name_field.value = ""
        course_field.value = ""
        year_level_field.value = None
        semester_field.value = "1st Semester"
        units.value = ""
        lab.value = "0"
        hands_on.value = "0"
        payment_input_field.value = ""

        for field in (student_id_field, student_name_field, course_field, year_level_field, semester_field, units, lab,
                      hands_on):
            set_error(field, None)

        navigate(0)

    for field in (lab, hands_on):
        field.on_change = lambda e: on_units_change(None)

    page.add(
        ft.Container(
            content=screen_area,
            padding=16,
            expand=True,
        )
    )

    render_screen()

if __name__ == "__main__":
    ft.run(main, assets_dir="assets")