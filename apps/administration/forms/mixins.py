from django import forms


class StyleFormMixin:
    """
    Mixin to apply Tailwind CSS styles to form fields.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()

    def apply_styles(self):
        for name, field in self.fields.items():
            widget = field.widget
            attrs = widget.attrs

            # Skip if class is already set manually in widget definition
            # (though often we want to merge, but simple check is okay for now)
            # Actually, the original code overwrites or updates. Let's update.

            css_class = attrs.get("class", "")

            if isinstance(widget, forms.CheckboxInput):
                if "toggle" not in css_class and "checkbox" not in css_class:
                    attrs.update({"class": css_class + " toggle toggle-success"})
            elif isinstance(widget, (forms.ClearableFileInput, forms.FileInput)):
                if "file-input" not in css_class:
                    attrs.update(
                        {"class": css_class + " file-input file-input-bordered w-full"}
                    )
            elif isinstance(widget, forms.CheckboxSelectMultiple):
                pass  # Special handling usually needed
            elif isinstance(widget, forms.Textarea):
                if "textarea" not in css_class:
                    attrs.update(
                        {"class": css_class + " textarea textarea-bordered w-full"}
                    )
            elif isinstance(widget, forms.Select):
                if "select" not in css_class:
                    attrs.update(
                        {"class": css_class + " select select-bordered w-full"}
                    )
            else:
                # Default input
                if "input" not in css_class:
                    attrs.update({"class": css_class + " input input-bordered w-full"})
