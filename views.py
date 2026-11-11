from django.db.models import F
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views import generic

from .forms import CommentForm
from .models import Choice, Question



class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """Return the last five published questions (not including those set to be
           published in the future)."""
        return Question.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[:5]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.COOKIES.get("visited_polls"):
            context["welcome_message"] = "Welcome back to the Polls application."
        else:
            context["welcome_message"] = "Welcome to the Polls application."

        # Count visits to the index page
        visit_count = self.request.session.get("visit_count", 0) + 1
        self.request.session["visit_count"] = visit_count
        context["visit_count"] = visit_count

        last_poll_id = self.request.session.get("last_viewed_poll_id")
        if last_poll_id:
            try:
                context["last_viewed_poll"] = Question.objects.get(pk=last_poll_id)
            except Question.DoesNotExist:
                context["last_viewed_poll"] = None
        return context

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        if not self.request.COOKIES.get("visited_polls"):
            response.set_cookie("visited_polls", "yes", max_age=120)
        return response




class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"

    def get_queryset(self):
        """

        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.request.session["last_viewed_poll_id"] = self.object.pk
        return context


class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"

def results(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, "polls/results.html", {"question": question})

def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )
    else:
        selected_choice.votes = F("votes") + 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))

class CommentCreateView(LoginRequiredMixin, generic.FormView):
    template_name = "polls/comment_form.html"
    form_class = CommentForm

    def dispatch(self, request, *args, **kwargs):
        self.question = get_object_or_404(
            Question,
            pk=kwargs["question_id"],
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["question"] = self.question
        return context

    def form_valid(self, form):
        comment = form.save(commit=False)
        comment.question = self.question
        comment.owner = self.request.user
        comment.save()

        return super().form_valid(form)

    def get_success_url(self):
        return reverse("polls:detail", args=[self.question.pk])


