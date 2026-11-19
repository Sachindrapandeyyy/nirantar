from typing import Any, Dict, List
from playwright.async_api import Page


class DOMParser:
    """
    Extracts interactive form fields (inputs, dropdowns, uploads) with associated labels.
    """

    @staticmethod
    async def extract_interactive_fields(page: Page) -> List[Dict[str, Any]]:
        """
        Executes in-browser JavaScript to extract clean interactive elements.
        """
        script = """
        () => {
            const fields = [];
            const elements = document.querySelectorAll('input, select, textarea');

            elements.forEach((el, index) => {
                // Ignore hidden inputs and submit buttons
                if (el.type === 'hidden' || el.type === 'submit' || el.style.display === 'none') {
                    return;
                }

                // Find associated label
                let labelText = '';
                if (el.id) {
                    const label = document.querySelector(`label[for="${el.id}"]`);
                    if (label) labelText = label.innerText.trim();
                }
                if (!labelText) {
                    const parentLabel = el.closest('label');
                    if (parentLabel) labelText = parentLabel.innerText.trim();
                }
                if (!labelText && el.getAttribute('aria-label')) {
                    labelText = el.getAttribute('aria-label').trim();
                }
                if (!labelText && el.getAttribute('placeholder')) {
                    labelText = el.getAttribute('placeholder').trim();
                }

                fields.push({
                    index: index,
                    id: el.id || '',
                    name: el.name || '',
                    type: el.type || el.tagName.toLowerCase(),
                    label: labelText,
                    placeholder: el.placeholder || '',
                    required: el.required || el.getAttribute('aria-required') === 'true',
                    tag: el.tagName.toLowerCase()
                });
            });

            return fields;
        }
        """
        try:
            return await page.evaluate(script)
        except Exception:
            return []
