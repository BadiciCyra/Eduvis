from flask import Flask, request, render_template, jsonify
import openai
from openai import OpenAI

# Set the OpenAI API key

client = OpenAI(api_key)
app = Flask(__name__)

# Upload file for fine-tuning
response = client.files.create(
    file=open("data.jsonl", "rb"),
    purpose="fine-tune"
)

print("File ID:", response.id)

# Create fine-tuning job
job = client.fine_tuning.jobs.create(
    training_file=response.id,
    model="gpt-3.5-turbo"
)

print("Fine-Tuning Job ID:", job.id)

if __name__ == '__main__':
    app.run(debug=True)
