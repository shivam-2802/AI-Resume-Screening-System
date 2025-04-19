import PyPDF2
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import UploadFileForm
from django.core.files.storage import FileSystemStorage
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from .models import JobTitle, Keyword, UploadedFile
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def clean_text(text):
    # Convert to lowercase
    text = text.lower()
    # Remove numbers and special characters (keep words and spaces only)
    text = re.sub(r'[^a-z\s]', '', text)
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()

    # Tokenize
    tokens = word_tokenize(text)

    # Remove stop words and lemmatize
    cleaned_tokens = [
        lemmatizer.lemmatize(token) 
        for token in tokens 
        if token not in stop_words and token.isalpha()
    ]

    return ' '.join(cleaned_tokens)


def handle_uploaded_files(request):
    if request.method == 'POST' and request.FILES.getlist('files'):
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            job_title = form.cleaned_data['job_title']
            uploaded_files = request.FILES.getlist('files')
            file_objects = []

            # Save files to model
            for uploaded_file in uploaded_files:
                fs = FileSystemStorage()
                filename = fs.save(uploaded_file.name, uploaded_file)
                file_url = fs.url(filename)

                # Create and save each file in the database
                uploaded_file_obj = UploadedFile(file=filename)
                uploaded_file_obj.save()
                file_objects.append(uploaded_file_obj)


            # Retrieve the job title selected by the employer
            job_title_id = request.POST.get('job_title')
            job_title = JobTitle.objects.get(id=job_title_id)
            
            # Retrieve keywords for the selected job title
            words = Keyword.objects.filter(job_title=job_title)
            keywords = str(words).lower()
            keyword_list = keywords.split()
            keyword_string = ' '.join(keyword_list)

            # Process each uploaded file
            extracted_texts = []
            for uploaded_file in file_objects:
                file_path = uploaded_file.file.path
                with open(file_path, 'rb') as f:
                    extracted_text = extract_text_from_pdf(f)
                    cleaned_text = clean_text(extracted_text)
                    ctext = str(cleaned_text).split()
                    cleaned_text_str = ' '.join(ctext)

                    documents = [keyword_string, cleaned_text_str]

                    # Create the TF-IDF matrix
                    vectorizer = TfidfVectorizer()
                    tfidf_matrix = vectorizer.fit_transform(documents)

                    # Compute cosine similarity between keyword vector and resume vector
                    cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

                    # Convert to percentage score (out of 100)
                    match_score = round(cosine_sim * 100, 2)

                    # Match cleaned text with keywords
                    matched_keywords = []
                    for keyword in ctext:
                        if keyword in keyword_list:
                            matched_keywords.append(keyword)
                
                    extracted_texts.append({
                        'filename': uploaded_file.file.name,
                        'text': cleaned_text,
                        'matched_keywords': matched_keywords,
                        'score': match_score
                    })

                    extracted_texts = sorted(extracted_texts, key=lambda x: x['score'], reverse=True)


            # Pass job title name to results page if needed
            return render(request, 'results.html', {
                'extracted_texts': extracted_texts,
                'job_title': job_title.title
            })

    # If GET or invalid POST
    return render(request, 'upload.html', {'form': UploadFileForm()})