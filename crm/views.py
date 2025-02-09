import json

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.contrib import messages

from .models import Customer
from .forms import CustomerForm

class CustomerListView(ListView):
    model = Customer
    template_name = 'crm/customer_list.html'
    context_object_name = 'customers'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            print(f"User {request.user.email} authenticated.")
            if not request.user.email_verified:
                messages.error(request, "Your email is not verified. Please verify your email.")
                return redirect("auth:login")
        else:
            print("User not authenticated.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):

        return Customer.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            ids_to_delete = data.get('ids', [])

            if ids_to_delete:

                deleted_count, _ = Customer.objects.filter(
                    id__in=ids_to_delete, user=request.user
                ).delete()

                if deleted_count > 0:
                    return JsonResponse({'success': True, 'deleted_count': deleted_count})
                else:
                    return JsonResponse({'success': False, 'error': 'You do not have permission to delete these entries'})

            return JsonResponse({'success': False, 'error': 'IDs for deletion not specified'})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

class CustomerDetailView(DetailView):
    model = Customer
    template_name = 'crm/customer_detail.html'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if obj.user != self.request.user:
            raise Http404("You do not have access to this entry.")
        return obj


class CustomerCreateView(CreateView):
    model = Customer
    template_name = 'crm/customer_form.html'
    form_class = CustomerForm

    def get_success_url(self):
        return reverse_lazy('crm:customer_detail', kwargs={'pk': self.object.pk})

    def form_invalid(self, form):
        errors = []
        for field, error_list in form.errors.items():
            for error in error_list:
                errors.append(f"{field.capitalize()}: {error}")
        return render(self.request, 'crm/customer_form.html', {'form': form, 'errors': errors})

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        return HttpResponseRedirect(reverse_lazy('crm:customer_list'))


class CustomerUpdateView(UpdateView):
    model = Customer
    template_name = 'crm/customer_edit.html'
    form_class = CustomerForm

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if obj.user != self.request.user:
            raise Http404("You cannot edit this entry.")
        return obj

    def form_invalid(self, form):
        errors = []
        for field, error_list in form.errors.items():
            for error in error_list:
                errors.append(f"{field.capitalize()}: {error}")
        return render(self.request, 'crm/customer_edit.html', {'form': form, 'errors': errors})

    def get_success_url(self):
        return reverse_lazy('crm:customer_detail', kwargs={'pk': self.object.pk})

class CustomerDeleteView(DeleteView):
    model = Customer
    template_name = 'crm/customer_confirm_delete.html'
    success_url = reverse_lazy('crm:customer_list')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if obj.user != self.request.user:
            raise Http404("You cannot remove this entry.")
        return obj

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            self.object.delete()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': True, 'message': 'Success'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

