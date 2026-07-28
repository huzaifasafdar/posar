frappe.query_reports["POS Tax Report"] = {
	collapsed_sections: {},
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "transaction_type",
			label: __("Show"),
			fieldtype: "Select",
			options: ["All", "Sales", "Purchase / Expense"],
			default: "All",
		},
		{
			fieldname: "only_pos",
			label: __("Only POS Invoices"),
			fieldtype: "Check",
			default: 1,
		},
		{
			fieldname: "pos_profile",
			label: __("POS Profile"),
			fieldtype: "Link",
			options: "POS Profile",
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
		},
		{
			fieldname: "supplier",
			label: __("Supplier"),
			fieldtype: "Link",
			options: "Supplier",
		},
		{
			fieldname: "tax_account",
			label: __("Tax Account"),
			fieldtype: "Link",
			options: "Account",
			get_query: function () {
				const company = frappe.query_report.get_filter_value("company");
				return {
					filters: {
						company: company,
						is_group: 0,
					},
				};
			},
		},
		{
			fieldname: "cashier",
			label: __("Cashier"),
			fieldtype: "Link",
			options: "User",
		},
	],
	after_datatable_render: function () {
		const report = frappe.query_report;
		const report_settings = frappe.query_reports["POS Tax Report"];

		if (report._pos_tax_raw_data !== report.raw_data) {
			report._pos_tax_raw_data = report.raw_data;
			report._pos_tax_all_rows = (report.data || []).slice();
		}

		report.$report.off("click", ".pos-tax-section-toggle");
		report.$report.on("click", ".pos-tax-section-toggle", function (event) {
			event.preventDefault();
			event.stopPropagation();

			const section = $(this).data("section");
			report_settings.collapsed_sections[section] = !report_settings.collapsed_sections[section];
			report.data = report_settings.get_visible_data(report._pos_tax_all_rows || report.data || []);
			report.render_datatable();
		});
	},
	get_visible_data: function (data) {
		const report_settings = frappe.query_reports["POS Tax Report"];
		let current_section = null;

		return (data || []).filter((row) => {
			if (row.is_section) {
				current_section = row.section;
				return true;
			}

			return !current_section || !report_settings.collapsed_sections[current_section];
		});
	},
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (data && data.is_section) {
			if (column.fieldname === "section") {
				const report_settings = frappe.query_reports["POS Tax Report"];
				const is_collapsed = report_settings.collapsed_sections[data.section];
				const icon = is_collapsed ? "right" : "down";

				return `
					<button
						class="btn btn-xs btn-default pos-tax-section-toggle"
						data-section="${frappe.utils.escape_html(data.section)}"
						style="margin-right: 6px;"
					>
						${frappe.utils.icon(icon, "xs")}
					</button>
					<b style="font-size: 13px;">${value}</b>
				`;
			}

			if (["taxable_amount", "tax_amount", "total_amount"].includes(column.fieldname)) {
				return value ? `<b>${value}</b>` : "";
			}

			return "";
		}

		if (data && data.is_summary) {
			return `<b>${value}</b>`;
		}

		return value;
	},
};
