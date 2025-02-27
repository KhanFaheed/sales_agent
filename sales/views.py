from django.shortcuts import render
from django.http import JsonResponse
from .agent import sales_agent

#create view here
def chat_view(request):
    if request.method == 'POST':
        user_message = request.POST.get('message')
        agent_response = sales_agent(user_message)
        return JsonResponse({'response': agent_response})
    return render(request, 'sales/chat.html')