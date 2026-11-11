from django import forms

from .models import Comment

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["comment_text"]

        labels = {
            "comment_text": "Comment",
        }

        widgets = {
            "comment_text": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Write your comment here...",
                }
            ),
        }

    def clean_comment_text(self):
        text = self.cleaned_data["comment_text"].strip()

        if not text:
            raise forms.ValidationError("Please enter a comment.")

        return text
