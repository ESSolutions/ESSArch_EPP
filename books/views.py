from django.views.generic import ListView, DetailView
from books.models import Publisher, Book

#class PublisherList(ListView):
#    model = Publisher
    
class PublisherDetailView(DetailView):

    context_object_name = "publisher"
    model = Publisher

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(PublisherDetailView, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['book_list'] = Book.objects.all()
        return context