import requests
import os
from django.contrib.auth.backends import BaseBackend
from .models import User

class TURESTAPIBackend(BaseBackend):
    def authenticate(self, request, tu_id=None, password=None):
        api_url = "https://restapi.tu.ac.th/api/v1/auth/Ad/verify"
        
        payload = {
            "UserName": tu_id,
            "PassWord": password
        }
        
        headers = {
            "Content-Type": "application/json", 
            "Application-Key": os.getenv("TU_APP_KEY")
        }
        
        try:
            response = requests.post(api_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                user_data = response.json() 

                if user_data.get('status') == True:

                    full_name = user_data.get('displayname_en', 'Unknown Name')
                    name_parts = full_name.split(maxsplit=1)
                    first = name_parts[0] if len(name_parts) > 0 else "Unknown"
                    last = name_parts[1] if len(name_parts) > 1 else "Unknown"
                    
                    api_role = user_data.get('type', 'Student').capitalize() 
                    
                    user, created = User.objects.get_or_create(
                        tu_id=user_data.get('username', tu_id),
                        defaults={
                            'first_name': first,
                            'last_name': last,
                            'email': user_data.get('email', f"{tu_id}@dome.tu.ac.th"),
                            'role': api_role,
                            'is_staff': False,
                            'is_superuser': False
                        }
                    )

                    if not created:
                        user.first_name = first
                        user.last_name = last
                        user.email = user_data.get('email', user.email)
                        user.role = api_role

                    user.save()
                    return user
                    
        except requests.exceptions.RequestException:

            return None
            
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None