import json
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.models import User
from .models import ChatbotConfig, ChatSession, ChatMessage, KnowledgeGap
from .forms import ChatbotConfigForm
from .utils import generate_response, calculate_confidence_score
from repo.models import Content, Folder

@login_required
def chatbot_home(request):
    """Chatbot dashboard home"""
    # Get or create chatbot config
    config, created = ChatbotConfig.objects.get_or_create(user=request.user)
    
    # Get recent chat sessions
    recent_sessions = ChatSession.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # Get unresolved knowledge gaps
    gaps = KnowledgeGap.objects.filter(user=request.user, is_resolved=False).order_by('-created_at')[:5]
    
    return render(request, 'chatbot/home.html', {
        'config': config,
        'recent_sessions': recent_sessions,
        'gaps': gaps
    })

@login_required
def chatbot_config(request):
    """Configure chatbot settings"""
    config, created = ChatbotConfig.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ChatbotConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            
            # Generate embed code
            host = request.get_host()
            protocol = 'https' if request.is_secure() else 'http'
            widget_url = f"{protocol}://{host}/chatbot/widget/{request.user.username}/"
            
            embed_code = f"""
            <script>
                (function() {{
                    var d = document, s = d.createElement('script');
                    s.src = '{widget_url}script.js';
                    s.async = true;
                    d.getElementsByTagName('body')[0].appendChild(s);
                }})();
            </script>
            <div id="edu-rag-chatbot"></div>
            """
            
            config.embed_code = embed_code
            config.save()
            
            messages.success(request, 'Chatbot configuration updated successfully!')
            return redirect('chatbot_home')
    else:
        form = ChatbotConfigForm(instance=config)
    
    return render(request, 'chatbot/config.html', {'form': form})

@login_required
def embed_code(request):
    """View embed code for chatbot"""
    try:
        config = ChatbotConfig.objects.get(user=request.user)
        return render(request, 'chatbot/embed_code.html', {'config': config})
    except ChatbotConfig.DoesNotExist:
        messages.error(request, 'Please configure your chatbot first.')
        return redirect('chatbot_config')

@login_required
def chatbot_test(request):
    """Test the chatbot within the admin portal"""
    try:
        config = ChatbotConfig.objects.get(user=request.user)
        # Create a new test session or get the latest
        session, created = ChatSession.objects.get_or_create(
            user=request.user,
            is_active=True,
            defaults={'session_id': f"test_{uuid.uuid4()}"}
        )
        
        return render(request, 'chatbot/test.html', {
            'config': config,
            'session': session
        })
    except ChatbotConfig.DoesNotExist:
        messages.error(request, 'Please configure your chatbot first.')
        return redirect('chatbot_config')

@csrf_exempt
def chat_api(request):
    """API endpoint for chatbot interactions"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        message = data.get('message')
        session_id = data.get('session_id')
        username = data.get('username')
        
        if not message or not (session_id or username):
            return JsonResponse({'error': 'Missing required parameters'}, status=400)
        
        # Handle public widget requests
        if username and not session_id:
            try:
                user = User.objects.get(username=username)
                # Create new session
                session_id = f"widget_{uuid.uuid4()}"
                session = ChatSession.objects.create(
                    user=user,
                    session_id=session_id,
                    is_active=True
                )
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)
        else:
            # Get existing session
            try:
                session = ChatSession.objects.get(session_id=session_id)
                user = session.user
            except ChatSession.DoesNotExist:
                return JsonResponse({'error': 'Invalid session'}, status=404)
        
        # Save user message
        user_message = ChatMessage.objects.create(
            session=session,
            message_type='user',
            content=message
        )
        
        # Generate response using RAG
        response_text, confidence = generate_response(user, message)
        
        # Save assistant message
        assistant_message = ChatMessage.objects.create(
            session=session,
            message_type='assistant',
            content=response_text,
            confidence_score=confidence
        )
        
        # Check if this is a knowledge gap
        config = ChatbotConfig.objects.get(user=user)
        if confidence < config.confidence_threshold:
            gap = KnowledgeGap.objects.create(
                user=user,
                question=message,
                confidence_score=confidence,
                chat_message=assistant_message
            )
        
        return JsonResponse({
            'response': response_text,
            'confidence': confidence,
            'session_id': session_id
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def knowledge_gaps(request):
    """View and manage knowledge gaps"""
    gaps = KnowledgeGap.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'chatbot/gaps.html', {'gaps': gaps})

@login_required
def resolve_gap(request, gap_id):
    """Mark a knowledge gap as resolved"""
    gap = get_object_or_404(KnowledgeGap, id=gap_id, user=request.user)
    
    if request.method == 'POST':
        gap.is_resolved = True
        gap.resolved_at = timezone.now()
        gap.save()
        messages.success(request, 'Knowledge gap marked as resolved.')
        return redirect('knowledge_gaps')
    
    return render(request, 'chatbot/resolve_gap.html', {'gap': gap})

def chatbot_widget(request, username):
    """Serve chatbot widget for public embedding"""
    try:
        user = User.objects.get(username=username)
        config = ChatbotConfig.objects.get(user=user)
        
        if request.path.endswith('script.js'):
            # Serve JavaScript for widget
            response = render(request, 'chatbot/widget_script.js', {
                'config': config,
                'username': username
            }, content_type='application/javascript')
            return response
        
        # Serve widget HTML
        return render(request, 'chatbot/widget.html', {
            'config': config,
            'username': username
        })
        
    except (User.DoesNotExist, ChatbotConfig.DoesNotExist):
        return JsonResponse({'error': 'Chatbot not found'}, status=404)