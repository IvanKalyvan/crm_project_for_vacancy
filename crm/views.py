from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Customer
from django.urls import reverse_lazy

class CustomerListView(ListView):
    model = Customer
    template_name = 'crm/customer_list.html'
    context_object_name = 'customers'

class CustomerDetailView(DetailView):
    model = Customer
    template_name = 'crm/customer_detail.html'

class CustomerCreateView(CreateView):

    model = Customer
    template_name = 'crm/customer_form.html'
    fields = ['name', 'email', 'phone']

    def get_success_url(self):

        return reverse_lazy('customer_detail', kwargs={'pk': self.object.pk})

class CustomerUpdateView(UpdateView):

    model = Customer
    template_name = 'crm/customer_form.html'
    fields = ['name', 'email', 'phone']

    def get_success_url(self):

        return reverse_lazy('customer_detail', kwargs={'pk': self.object.pk})

class CustomerDeleteView(DeleteView):
    model = Customer
    template_name = 'crm/customer_confirm_delete.html'
    success_url = reverse_lazy('customer_list')
