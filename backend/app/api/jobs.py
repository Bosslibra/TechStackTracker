from flask import Blueprint, jsonify, request
from tech_stack_tracker.app.services.auth import csrf_protect, login_required

from ..services.jobs import read_jobs, write_jobs

jobs_bp = Blueprint("jobs", __name__)


@jobs_bp.route("/api/jobs", methods=["GET"])
def get_jobs():
    """
    Retrieve a list of jobs.

    Returns:
        200 OK with JSON containing a list of job objects.
    """

    return jsonify(read_jobs()), 200

# TODO: Add a get /api/jobs/<job_id> endpoint to retrieve details for a specific job.


@jobs_bp.route('/api/jobs', methods=['POST'])
@login_required
@csrf_protect   
def save_jobs():
    payload = request.get_json(silent=True)
    if not isinstance(payload, list):
        return jsonify({'error': 'Expected a JSON array'}), 400

    write_jobs(payload)
    return '', 204
