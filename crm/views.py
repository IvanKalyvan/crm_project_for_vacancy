from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import render
from django.http import HttpResponseRedirect

from .models import Customer

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

    def form_invalid(self, form):

        errors = []
        for field, error_list in form.errors.items():
            for error in error_list:
                errors.append(f"{field.capitalize()}: {error}")

        return render(self.request, 'crm/customer_form.html', {'form': form, 'errors': errors})

    def form_valid(self, form):

        return HttpResponseRedirect(reverse_lazy('customer_list'))

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
