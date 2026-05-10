from flask import Flask, render_template, request, jsonify
import urllib.request
import urllib.error
import json

app = Flask(__name__)

OPENROUTER_KEY = "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"  # Get free key at openrouter.ai → Keys → Create
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openrouter/auto"  # Auto-picks a working free model every time

results_history = []


def ask_ai(messages, system=None, max_tokens=600):
    ai_messages = []

    if system:
        ai_messages.append({"role": "system", "content": system})

    for msg in messages:
        ai_messages.append({"role": msg["role"], "content": msg["content"]})

    payload = json.dumps({
        "model": OPENROUTER_MODEL,
        "messages": ai_messages,
        "max_tokens": max_tokens,
        "temperature": 0.7
    }).encode("utf-8")

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "CalmMind"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[AI ERROR {e.code}] {body}")
        raise RuntimeError(f"AI {e.code}: {body}")
    except Exception as e:
        print(f"[AI ERROR] {type(e).__name__}: {e}")
        raise


@app.route('/api/test')
def api_test():
    try:
        reply = ask_ai([{"role": "user", "content": "Say hello in one sentence."}], max_tokens=50)
        return jsonify({"status": "OK", "reply": reply})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/test', methods=['GET', 'POST'])
def test():
    result = None
    if request.method == 'POST':
        q1 = int(request.form.get('q1'))
        q2 = int(request.form.get('q2'))
        q3 = int(request.form.get('q3'))
        score = q1 + q2 + q3
        if score <= 2:   result = "Low Anxiety 😊"
        elif score <= 5: result = "Moderate Anxiety 😐"
        else:            result = "High Anxiety 😟"
        results_history.append({"q1": q1, "q2": q2, "q3": q3, "score": score, "result": result})
    return render_template('test.html', result=result)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', results=results_history)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/resources')
def resources():
    return render_template('resources.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    message = None
    if request.method == 'POST':
        name = request.form.get('name')
        message = f"Thanks {name}, your feedback has been received!"
    return render_template('contact.html', message=message)

@app.route('/mindfulness')
def mindfulness():
    return render_template('mindfulness.html')

@app.route('/stress')
def stress():
    return render_template('stress.html')

@app.route('/anxiety')
def anxiety():
    return render_template('anxiety.html')

@app.route('/mood')
def mood():
    return render_template('mood.html')

@app.route('/selfcare')
def selfcare():
    return render_template('selfcare.html')

@app.route('/analyze')
def analyze():
    return render_template('analyze.html')

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/detect')
def detect():
    return render_template('detect.html')

@app.route('/psychologist')
def psychologist():
    return render_template('psychologist.html')

@app.route('/recommendations')
def recommendations():
    return render_template('recommendations.html')


@app.route('/api/detect', methods=['POST'])
def api_detect():
    body    = request.get_json()
    domains = body.get('domains', [])
    pct     = body.get('pct', 50)

    system = "You are a clinical psychologist AI. Reply with ONLY raw JSON, no markdown, no extra text."

    prompt = (
        "User mental health screening (0=best, 3=worst): "
        + ", ".join(d['cat'] + ": " + str(d['score']) + "/3" for d in domains)
        + ". Overall severity: " + str(pct) + "%. "
        + "Reply with ONLY this JSON, no markdown, no extra text: "
        + '{"overall":"Low","emoji":"😊","summary":"2 compassionate sentences here.",'
        + '"mood_pct":30,"anxiety_pct":40,"stress_pct":35,"color":"#10b981"}'
        + " Rules: overall=Low/Moderate/Elevated/High."
        + " color: #10b981=Low, #f59e0b=Moderate, #f97316=Elevated, #ef4444=High"
    )

    try:
        text   = ask_ai([{"role": "user", "content": prompt}], system=system, max_tokens=300)
        clean  = text.strip().replace("```json","").replace("```","").strip()
        result = json.loads(clean)
        return jsonify(result)
    except Exception as e:
        print(f"[DETECT ERROR] {e}")
        overall = "Low" if pct < 30 else "Moderate" if pct < 55 else "Elevated" if pct < 75 else "High"
        color   = "#10b981" if pct < 30 else "#f59e0b" if pct < 55 else "#f97316" if pct < 75 else "#ef4444"
        return jsonify({
            "overall": overall, "emoji": "😐",
            "summary": "Based on your responses we have assessed your current mental state. Remember seeking support is always a sign of strength.",
            "mood_pct":    min(100, (domains[0]['score'] if domains else 1) * 33),
            "anxiety_pct": min(100, (domains[1]['score'] if len(domains) > 1 else 1) * 33),
            "stress_pct":  min(100, (domains[4]['score'] if len(domains) > 4 else 1) * 33),
            "color": color
        })


@app.route('/api/psychologist/open', methods=['POST'])
def api_psychologist_open():
    body       = request.get_json()
    topic      = body.get('topic', 'general mental wellness')
    assessment = body.get('assessment', None)

    context = ""
    if assessment:
        context = (
            f"User assessment: {assessment.get('overall','unknown')} distress, "
            f"mood {assessment.get('mood_pct',50)}%, anxiety {assessment.get('anxiety_pct',50)}%, "
            f"stress {assessment.get('stress_pct',50)}%."
        )

    system = (
        f"You are Dr. Aria, a warm compassionate AI psychologist. "
        f"Session topic: {topic}. {context} "
        f"Speak calmly and empathetically. Short clear sentences. "
        f"Ask open-ended questions. Never diagnose. Validate feelings. 2-4 sentences only."
    )

    prompt = (
        f'Give a warm 2-sentence opening greeting for a therapy session about "{topic}". '
        f'{"Be especially warm — person has shown distress." if assessment else ""} '
        f'End with one gentle open question about {topic}.'
    )

    try:
        reply = ask_ai([{"role": "user", "content": prompt}], system=system, max_tokens=200)
        return jsonify({"reply": reply})
    except Exception as e:
        print(f"[OPEN ERROR] {e}")
        return jsonify({"reply": f"Hello, I am so glad you are here. This is a safe space to talk about {topic}. What has been on your mind lately?"})


@app.route('/api/psychologist/chat', methods=['POST'])
def api_psychologist_chat():
    body       = request.get_json()
    topic      = body.get('topic', 'general mental wellness')
    history    = body.get('history', [])
    assessment = body.get('assessment', None)

    context = ""
    if assessment:
        context = (
            f"User: {assessment.get('overall','unknown')} distress, "
            f"mood {assessment.get('mood_pct',50)}%, anxiety {assessment.get('anxiety_pct',50)}%, "
            f"stress {assessment.get('stress_pct',50)}%."
        )

    system = (
        f"You are Dr. Aria, a warm compassionate AI psychologist. "
        f"Session topic: {topic}. {context} "
        f"Be empathetic. 2-4 sentence responses. "
        f"Ask one follow-up question about {topic}. "
        f"Never diagnose. Validate emotions. Speak like a caring therapist."
    )

    try:
        reply = ask_ai(history, system=system, max_tokens=300)
        return jsonify({"reply": reply})
    except Exception as e:
        print(f"[CHAT ERROR] {e}")
        return jsonify({"reply": "I hear you.", "error": str(e)}), 500


@app.route('/api/recommendations', methods=['POST'])
def api_recommendations():
    body       = request.get_json()
    assessment = body.get('assessment', {})

    system = "You are a mental health advisor. Reply with ONLY raw JSON, no markdown, no extra text."

    prompt = (
        "User: distress=" + assessment.get('overall','Moderate')
        + ", mood=" + str(assessment.get('mood_pct',50)) + "%"
        + ", anxiety=" + str(assessment.get('anxiety_pct',50)) + "%"
        + ", stress=" + str(assessment.get('stress_pct',50)) + "%. "
        + "Reply with ONLY raw JSON, no markdown: "
        + '{"recommendations":[{"icon":"🧘","tag":"cat","title":"title","desc":"2 sentences.","link":"/mindfulness","color":"#6c63ff"}],'
        + '"daily_plan":[{"time":"7:00 AM","title":"act","desc":"desc","duration":"10 min"}]} '
        + "Give exactly 6 recommendations and 6 daily_plan items tailored to those distress levels."
    )

    try:
        text   = ask_ai([{"role": "user", "content": prompt}], system=system, max_tokens=1200)
        clean  = text.strip().replace("```json","").replace("```","").strip()
        result = json.loads(clean)
        return jsonify(result)
    except Exception as e:
        print(f"[RECS ERROR] {e}")
        return jsonify({
            "recommendations": [
                {"icon":"🧘","tag":"Mindfulness","title":"Daily Meditation","desc":"Start with 5 minutes of breathing each morning. Consistency matters more than duration.","link":"/mindfulness","color":"#6c63ff"},
                {"icon":"🌬️","tag":"Breathing","title":"Box Breathing","desc":"Inhale 4 hold 4 exhale 4. Calms your nervous system within minutes.","link":"/anxiety","color":"#00c9a7"},
                {"icon":"📓","tag":"Journaling","title":"Gratitude Journal","desc":"Write 3 things you are grateful for each night. Rewires the brain toward positivity.","link":"/mood","color":"#f59e0b"},
                {"icon":"🚶","tag":"Movement","title":"20-Min Daily Walk","desc":"Walking in nature reduces cortisol and boosts serotonin.","link":"/selfcare","color":"#10b981"},
                {"icon":"😴","tag":"Sleep","title":"Sleep Hygiene","desc":"Consistent sleep times regulate your circadian rhythm and improve mood.","link":"/selfcare","color":"#8b83ff"},
                {"icon":"💬","tag":"Therapy","title":"AI Therapy Session","desc":"Talk through your feelings with Dr. Aria regularly.","link":"/psychologist","color":"#ef4444"},
            ],
            "daily_plan": [
                {"time":"7:00 AM","title":"Morning Breathing","desc":"5 min box breathing","duration":"5 min"},
                {"time":"8:00 AM","title":"Healthy Breakfast","desc":"Nourish your brain","duration":"20 min"},
                {"time":"10:00 AM","title":"Mindfulness Break","desc":"Body scan exercise","duration":"5 min"},
                {"time":"1:00 PM","title":"Lunch Walk","desc":"Short walk outside","duration":"15 min"},
                {"time":"6:00 PM","title":"Relaxation","desc":"Yoga or stretching","duration":"20 min"},
                {"time":"9:30 PM","title":"Gratitude Journal","desc":"Write 3 good things","duration":"10 min"},
            ]
        })


@app.route('/chat', methods=['POST'])
def chat():
    data         = request.get_json()
    user_message = data.get("message", "")
    history      = data.get("history", [])

    system = (
        "You are CalmMind Assistant, a friendly and empathetic mental health chatbot for the CalmMind website. "
        "You help users with mood tracking, stress management, mindfulness, anxiety, and self-care. "
        "The website has these pages: /detect (AI mental health check), /psychologist (talk to Dr. Aria, AI therapist), "
        "/recommendations (personalised wellness plan), /mood, /stress, /mindfulness, /anxiety, /selfcare, /dashboard. "
        "Keep responses short (2-3 sentences max), warm, and supportive. "
        "If someone asks who or what you are, introduce yourself as CalmMind Assistant, a supportive mental wellness chatbot. "
        "Suggest relevant pages when appropriate. Never diagnose or replace professional help."
    )

    messages = history + [{"role": "user", "content": user_message}]

    try:
        reply = ask_ai(messages, system=system, max_tokens=150)
    except Exception as e:
        print(f"[CHAT ERROR] {e}")
        reply = "I'm here to help with mood, stress, mindfulness, anxiety, and our AI features. How can I support you today?"

    return jsonify({"reply": reply})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
