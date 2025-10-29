from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), default="")
    priority = db.Column(db.String(10), nullable=False, default="Medium")
    due_date = db.Column(db.String(20), default="")
    completed = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default="Pending")


with app.app_context():
    db.create_all()


@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    priority = (data.get("priority") or "").strip()
    if not title:
        return jsonify({"error": "title required"}), 400
    if priority not in ("Low", "Medium", "High"):
        return jsonify({"error": "priority required and must be Low/Medium/High"}), 400

    t = Task(
        title=title,
        description=(data.get("description") or "").strip(),
        priority=priority,
        due_date=data.get("due_date", ""),
        completed=bool(data.get("completed", False)),
    )
    t.status = "Completed" if t.completed else "Pending"
    db.session.add(t)
    db.session.commit()
    return jsonify({"message": "task created", "id": t.id}), 201


@app.route("/tasks", methods=["GET"])
def list_tasks():
    tasks = Task.query.order_by(Task.id.desc()).all()
    out = []
    for t in tasks:
        out.append(
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "priority": t.priority,
                "due_date": t.due_date,
                "completed": t.completed,
                "status": "Completed" if t.completed else "Pending",
            }
        )
    return jsonify(out)


@app.route("/tasks/<int:task_id>", methods=["PATCH"])
def patch_task(task_id):
    data = request.get_json() or {}
    t = Task.query.get_or_404(task_id)
    changed = False

    if "completed" in data:
        val = data["completed"]
        if isinstance(val, str):
            val_l = val.lower()
            new_completed = val_l == "true"
        else:
            new_completed = bool(val)
        t.completed = new_completed
        t.status = "Completed" if t.completed else "Pending"
        changed = True

    if "priority" in data and data["priority"] in ("Low", "Medium", "High"):
        t.priority = data["priority"]
        changed = True

    if "due_date" in data:
        t.due_date = data["due_date"]
        changed = True

    if changed:
        db.session.commit()

    return jsonify({"message": "task updated"})


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    t = Task.query.get_or_404(task_id)
    db.session.delete(t)
    db.session.commit()
    return jsonify({"message": "deleted"})


@app.route("/insights", methods=["GET"])
def insights():
    total = Task.query.count()
    completed = Task.query.filter_by(completed=True).count()
    pending = total - completed
    return jsonify({
        "total": total,
        "completed": completed,
        "pending": pending,
        "summary": f"You have {pending} pending and {completed} completed tasks out of {total}."
    })


if __name__ == "__main__":
    app.run(debug=True)
