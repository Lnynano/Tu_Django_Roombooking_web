from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

#this comment is made to be delete
def send_email_page(request):
    if request.method == "POST":
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        if not email or not subject or not message:
            messages.error(request, "Please fill in all fields.")
            return redirect("send_email_page")

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        messages.success(request, "Email sent successfully.")
        return redirect("send_email_page")

    return render(request, "emails/send_email.html")