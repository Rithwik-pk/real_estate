/**
 * AI Portfolio Query Widget (Feature N).
 * Rendered in the Real Estate workspace via a custom page/widget.
 * Calls real_estate.ai.portfolio_query.ask_portfolio and displays the streaming result.
 */
frappe.provide('real_estate');

real_estate.PortfolioQueryWidget = class {
    constructor(wrapper) {
        this.wrapper = wrapper;
        this.render();
    }

    render() {
        this.wrapper.innerHTML = `
            <div class="re-portfolio-query p-3">
                <h6 class="mb-2 text-muted">
                    <i class="fa fa-robot me-1"></i> Ask about your portfolio (AI)
                </h6>
                <div class="input-group mb-2">
                    <input type="text" id="re-query-input" class="form-control form-control-sm"
                        placeholder="e.g. Which units have been vacant for more than 30 days?"
                        style="border-radius:4px 0 0 4px"/>
                    <button class="btn btn-primary btn-sm" id="re-query-btn"
                        style="border-radius:0 4px 4px 0">Ask</button>
                </div>
                <div id="re-query-result" class="bg-light rounded p-2"
                    style="min-height:60px;font-size:0.85rem;white-space:pre-wrap;display:none"></div>
                <div id="re-query-spinner" style="display:none">
                    <span class="spinner-border spinner-border-sm me-1"></span> Thinking...
                </div>
            </div>
        `;
        this.wrapper.querySelector('#re-query-btn').addEventListener('click', () => this.ask());
        this.wrapper.querySelector('#re-query-input').addEventListener('keydown', e => {
            if (e.key === 'Enter') this.ask();
        });
    }

    ask() {
        const input = this.wrapper.querySelector('#re-query-input');
        const result = this.wrapper.querySelector('#re-query-result');
        const spinner = this.wrapper.querySelector('#re-query-spinner');
        const question = input.value.trim();
        if (!question) return;

        result.style.display = 'none';
        result.textContent = '';
        spinner.style.display = 'block';

        frappe.call({
            method: 'real_estate.ai.portfolio_query.ask_portfolio',
            args: { question },
            callback(r) {
                spinner.style.display = 'none';
                if (r.message) {
                    result.textContent = r.message;
                    result.style.display = 'block';
                }
            },
            error() {
                spinner.style.display = 'none';
                result.textContent = 'Error querying AI. Please check your configuration.';
                result.style.display = 'block';
            },
        });
    }
};

// Auto-init on Real Estate workspace
frappe.pages['Real Estate'] && frappe.pages['Real Estate'].on_page_load && (function () {
    const page = frappe.pages['Real Estate'];
    const container = document.createElement('div');
    page.wrapper.querySelector('.layout-main').appendChild(container);
    new real_estate.PortfolioQueryWidget(container);
})();
