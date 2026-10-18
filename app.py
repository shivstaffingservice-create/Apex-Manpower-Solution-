import os, sqlite3
from functools import wraps
from flask import Flask, request, redirect, url_for, session, flash, render_template_string, g
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'replace-before-deployment')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('COOKIE_SECURE', '0') == '1'
CSRFProtect(app)
DB = os.environ.get('DATABASE_PATH', os.path.join(os.path.dirname(__file__), 'apex.db'))

def conn():
    if 'conn' not in g:
        g.conn = sqlite3.connect(DB)
        g.conn.row_factory = sqlite3.Row
    return g.conn

@app.teardown_appcontext
def close_db(error=None):
    c = g.pop('conn', None)
    if c: c.close()

def init_db():
    c = sqlite3.connect(DB)
    c.executescript('''
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, company TEXT NOT NULL, contact TEXT NOT NULL, email TEXT UNIQUE NOT NULL, phone TEXT, address TEXT, gst TEXT, password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'client');
    CREATE TABLE IF NOT EXISTS staff(id INTEGER PRIMARY KEY, full_name TEXT NOT NULL, phone TEXT, role TEXT NOT NULL, experience TEXT, location TEXT, availability TEXT DEFAULT 'Available');
    CREATE TABLE IF NOT EXISTS requests(id INTEGER PRIMARY KEY, client_id INTEGER NOT NULL REFERENCES users(id), job_role TEXT NOT NULL, staff_count INTEGER NOT NULL, experience TEXT, work_location TEXT NOT NULL, start_date TEXT, service_duration TEXT, instructions TEXT, status TEXT DEFAULT 'New Request', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    ''')
    email, password = os.environ.get('ADMIN_EMAIL','').lower(), os.environ.get('ADMIN_PASSWORD','')
    if email and password and not c.execute('SELECT id FROM users WHERE email=?',(email,)).fetchone():
        c.execute('INSERT INTO users(company,contact,email,password_hash,role) VALUES(?,?,?,?,?)',
                  ('Apex Manpower Solution','HR Admin',email,generate_password_hash(password),'admin'))
    c.commit(); c.close()
init_db()

def required(role=None):
    def deco(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            if not session.get('uid'):
                flash('Please log in first.'); return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash('Access denied.'); return redirect(url_for('home'))
            return fn(*a, **kw)
        return wrapper
    return deco

STYLE = '''
<style>
*{box-sizing:border-box}body{margin:0;background:#f5f7fa;color:#182f43;font:15px Arial,sans-serif}
nav{background:#102a43;color:white;padding:18px max(5%,20px);display:flex;justify-content:space-between;gap:15px;align-items:center}
nav a{color:white;text-decoration:none;margin-left:16px;font-weight:bold}.brand{font-size:20px;letter-spacing:1px}
main{max-width:1150px;margin:35px auto;padding:0 20px}.hero{background:#e9eff7;padding:55px;border-radius:16px}
h1{font-size:44px;margin:12px 0;color:#102a43}h2{color:#102a43}p{line-height:1.6;color:#657788}
.card{background:white;border:1px solid #e0e7ee;border-radius:12px;padding:24px;margin:16px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}
input,select,textarea{width:100%;padding:12px;border:1px solid #d5dee7;border-radius:6px;margin:6px 0 14px}
label{font-size:12px;font-weight:bold}button,.btn{background:#245cce;color:white;border:0;padding:12px 17px;border-radius:6px;cursor:pointer;text-decoration:none;font-weight:bold}
.secondary{background:#fff;color:#102a43;border:1px solid #cbd6e1}.muted{font-size:12px;color:#6b7d8c}
table{width:100%;border-collapse:collapse;background:white}th,td{text-align:left;padding:12px;border-bottom:1px solid #e5ebf0;font-size:13px;vertical-align:top}th{background:#edf2f7}
.flash{padding:12px;background:#fff3d7;border-radius:6px;margin-bottom:10px}.tag{background:#eaf0ff;padding:6px 8px;border-radius:5px;font-size:11px}
@media(max-width:600px){h1{font-size:34px}.hero{padding:25px}nav{align-items:flex-start;flex-direction:column}nav a{margin:0 12px 0 0}}
</style>'''
BASE = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Apex Manpower Solution provides staffing services for businesses."><title>{{ title }} | Apex Manpower Solution</title>''' + STYLE + '''</head><body><nav><a class="brand" href="/">APEX <small>MANPOWER SOLUTION</small></a><div><a href="/">Home</a>{% if session.get('uid') %}<a href="{{ url_for('admin') if session.get('role')=='admin' else url_for('client') }}">Dashboard</a><form method="post" action="/logout" style="display:inline"><input type="hidden" name="csrf_token" value="{{ csrf_token() }}"><button>Log out</button></form>{% else %}<a href="/login">Login</a><a href="/register">Register</a>{% endif %}</div></nav><main>{% for m in get_flashed_messages() %}<div class="flash">{{m}}</div>{% endfor %}{{ body|safe }}</main><footer style="background:#102a43;color:white;padding:25px 5%;margin-top:50px">APEX MANPOWER SOLUTION · Right People. Right Workplace.</footer></body></html>'''
def page(title, body, **ctx):
    return render_template_string(BASE, title=title, body=render_template_string(body, **ctx), **ctx)

@app.route('/')
def home():
    body = '''<section class="hero"><p>YOUR WORKFORCE PARTNER</p><h1>Right people.<br><span style="color:#245cce">Right workplace.</span></h1><p>Reliable staffing solutions for hotels, restaurants, retail, offices, warehouses, hospitals and more.</p><a class="btn" href="/register">Request Staff ↗</a> <a class="btn secondary" href="/login">Client Login</a></section><section class="grid"><div class="card"><h2>Hospitality</h2><p>Waiters, cooks, chefs, housekeeping and helpers.</p></div><div class="card"><h2>Office & Retail</h2><p>Office support, cashiers, store staff and front desk.</p></div><div class="card"><h2>Operations</h2><p>Warehouse helpers, cleaners, security and general workers.</p></div><div class="card"><h2>Managed Staffing</h2><p>Track requests, staff allocation and service updates.</p></div></section>'''
    return page('Home', body)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        f=request.form; pw=f.get('password','')
        if len(pw)<10 or not all(f.get(k,'').strip() for k in ['company','contact','email','phone','address']):
            flash('Complete required fields. Password must be at least 10 characters.')
        else:
            try:
                conn().execute('INSERT INTO users(company,contact,email,phone,address,gst,password_hash,role) VALUES(?,?,?,?,?,?,?,?)',
                (f['company'].strip(),f['contact'].strip(),f['email'].strip().lower(),f['phone'],f['address'],f.get('gst',''),generate_password_hash(pw),'client'))
                conn().commit(); flash('Account created. Please log in.'); return redirect('/login')
            except sqlite3.IntegrityError: flash('This email is already registered.')
    body='''<div class="card" style="max-width:560px;margin:auto"><h2>Create client account</h2><form method="post"><input type="hidden" name="csrf_token" value="{{csrf_token()}}">{% for key,label in [('company','Company / organization'),('contact','Contact person'),('email','Email address'),('phone','Mobile number'),('address','Business address'),('gst','GST number (optional)')] %}<label>{{label}}</label><input name="{{key}}" {% if key!='gst' %}required{% endif %} {% if key=='email' %}type="email"{% endif %}>{% endfor %}<label>Password (minimum 10 characters)</label><input type="password" name="password" minlength="10" required><button>Create account</button></form></div>'''
    return page('Register',body)

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        u=conn().execute('SELECT * FROM users WHERE email=?',(request.form.get('email','').strip().lower(),)).fetchone()
        if u and check_password_hash(u['password_hash'],request.form.get('password','')):
            session.clear(); session['uid']=u['id']; session['role']=u['role']; session['company']=u['company']
            return redirect('/admin' if u['role']=='admin' else '/client')
        flash('Email or password is incorrect.')
    body='''<div class="card" style="max-width:480px;margin:auto"><h2>Secure sign in</h2><p>Client and HR admin access</p><form method="post"><input type="hidden" name="csrf_token" value="{{csrf_token()}}"><label>Email</label><input type="email" name="email" required><label>Password</label><input type="password" name="password" required><button>Sign in securely</button></form></div>'''
    return page('Login',body)

@app.route('/logout',methods=['POST'])
@required()
def logout():
    session.clear(); return redirect('/')

@app.route('/client')
@required('client')
def client():
    reqs=conn().execute('SELECT * FROM requests WHERE client_id=? ORDER BY id DESC',(session['uid'],)).fetchall()
    body='''<h1>Client dashboard</h1><p>Welcome, {{session.get('company')}}. Submit a requirement and track updates.</p><div class="grid"><section class="card"><h2>Request staff</h2><form method="post" action="/request"><input type="hidden" name="csrf_token" value="{{csrf_token()}}"><label>Job role</label><input name="job_role" required placeholder="Waiter, cook, cleaner..."><label>Number of staff</label><input name="staff_count" type="number" min="1" max="1000" required><label>Experience</label><input name="experience"><label>Work location</label><input name="work_location" required><label>Start date</label><input name="start_date" type="date"><label>Service duration</label><select name="service_duration"><option>Temporary</option><option>Permanent</option></select><label>Instructions</label><textarea name="instructions"></textarea><button>Submit requirement</button></form></section><section class="card"><h2>Your staffing requests</h2>{% if reqs %}{% for r in reqs %}<p><b>#{{r.id}} · {{r.job_role}}</b> <span class="tag">{{r.status}}</span><br>{{r.staff_count}} staff · {{r.work_location}}<br><small>{{r.created_at}}</small></p><hr>{% endfor %}{% else %}<p>Your requests will appear here.</p>{% endif %}</section></div>'''
    return page('Client Dashboard',body,reqs=reqs)

@app.route('/request',methods=['POST'])
@required('client')
def request_staff():
    f=request.form
    try: n=int(f.get('staff_count','0'))
    except ValueError: n=0
    if n<1 or n>1000 or not f.get('job_role','').strip() or not f.get('work_location','').strip():
        flash('Enter a valid job role, staff count and location.'); return redirect('/client')
    conn().execute('INSERT INTO requests(client_id,job_role,staff_count,experience,work_location,start_date,service_duration,instructions) VALUES(?,?,?,?,?,?,?,?)',
    (session['uid'],f['job_role'],n,f.get('experience',''),f['work_location'],f.get('start_date',''),f.get('service_duration',''),f.get('instructions','')))
    conn().commit(); flash('Staff requirement submitted to Apex HR.'); return redirect('/client')

@app.route('/admin')
@required('admin')
def admin():
    c=conn()
    clients=c.execute("SELECT * FROM users WHERE role='client' ORDER BY id DESC").fetchall()
    staff=c.execute('SELECT * FROM staff ORDER BY id DESC').fetchall()
    reqs=c.execute("SELECT r.*,u.company,u.contact,u.email,u.phone FROM requests r JOIN users u ON u.id=r.client_id ORDER BY r.id DESC").fetchall()
    stats=[len(clients),len(staff),sum(1 for r in reqs if r['status']=='New Request'),sum(1 for r in reqs if r['status'] in ('Staff Assigned','Deployment Scheduled','Service Active'))]
    body='''<h1>HR admin dashboard</h1><p>Restricted internal database · only authorized HR admin can access this page.</p><div class="grid">{% for label,value in [('Clients',stats[0]),('Staff profiles',stats[1]),('New requests',stats[2]),('Active deployments',stats[3])] %}<div class="card"><p>{{label}}</p><h1>{{value}}</h1></div>{% endfor %}</div><div class="grid"><section class="card"><h2>Add staff profile</h2><form method="post" action="/admin/staff"><input type="hidden" name="csrf_token" value="{{csrf_token()}}"><label>Full name</label><input name="full_name" required><label>Job role</label><input name="role" required><label>Phone</label><input name="phone"><label>Experience</label><input name="experience"><label>Location</label><input name="location"><label>Availability</label><select name="availability"><option>Available</option><option>Assigned</option><option>Unavailable</option></select><button>Save staff</button></form></section><section class="card"><h2>Staff database ({{staff|length}})</h2><table><tr><th>Name</th><th>Role</th><th>Phone</th><th>Availability</th></tr>{% for s in staff %}<tr><td>{{s.full_name}}</td><td>{{s.role}}</td><td>{{s.phone}}</td><td>{{s.availability}}</td></tr>{% endfor %}</table></section></div><section class="card"><h2>Client database ({{clients|length}})</h2><div style="overflow:auto"><table><tr><th>Company</th><th>Contact</th><th>Email</th><th>Phone</th><th>Address</th><th>GST</th></tr>{% for c in clients %}<tr><td>{{c.company}}</td><td>{{c.contact}}</td><td>{{c.email}}</td><td>{{c.phone}}</td><td>{{c.address}}</td><td>{{c.gst}}</td></tr>{% endfor %}</table></div></section><section class="card"><h2>All staffing requests ({{reqs|length}})</h2><div style="overflow:auto"><table><tr><th>Client</th><th>Requirement</th><th>Location</th><th>Status</th><th>Update</th></tr>{% for r in reqs %}<tr><td>{{r.company}}<br>{{r.contact}}<br>{{r.email}}</td><td>{{r.job_role}} · {{r.staff_count}} staff<br>{{r.experience}}</td><td>{{r.work_location}}<br>{{r.start_date}}</td><td><span class="tag">{{r.status}}</span></td><td><form method="post" action="/admin/status/{{r.id}}"><input type="hidden" name="csrf_token" value="{{csrf_token()}}"><select name="status">{% for s in ['New Request','Under Review','Quotation Sent','Quotation Approved','Staff Assigned','Deployment Scheduled','Service Active','Completed','Rejected'] %}<option {% if r.status==s %}selected{% endif %}>{{s}}</option>{% endfor %}</select><button>Update</button></form></td></tr>{% endfor %}</table></div></section>'''
    return page('HR Admin',body,clients=clients,staff=staff,reqs=reqs,stats=stats)

@app.route('/admin/staff',methods=['POST'])
@required('admin')
def add_staff():
    f=request.form
    if not f.get('full_name','').strip() or not f.get('role','').strip():
        flash('Staff name and role are required.'); return redirect('/admin')
    conn().execute('INSERT INTO staff(full_name,phone,role,experience,location,availability) VALUES(?,?,?,?,?,?)',
    (f['full_name'],f.get('phone',''),f['role'],f.get('experience',''),f.get('location',''),f.get('availability','Available')))
    conn().commit(); flash('Staff profile added.'); return redirect('/admin')

@app.route('/admin/status/<int:rid>',methods=['POST'])
@required('admin')
def status(rid):
    allowed=['New Request','Under Review','Quotation Sent','Quotation Approved','Staff Assigned','Deployment Scheduled','Service Active','Completed','Rejected']
    s=request.form.get('status')
    if s in allowed:
        conn().execute('UPDATE requests SET status=? WHERE id=?',(s,rid)); conn().commit(); flash('Request status updated.')
    return redirect('/admin')

@app.route('/robots.txt')
def robots():
    return app.response_class('User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n',mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap():
    base=os.environ.get('SITE_URL',request.url_root.rstrip('/'))
    return app.response_class(f'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{base}/</loc></url></urlset>',mimetype='application/xml')

if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT','5000')),debug=False)
