from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask import request
import boto3, botocore, os, csv, json
from config import S3_BUCKET,S3_KEY,S3_SECRET
from filters import dateformat, gettype
from scripts import calacas_chidas


s3 = boto3.client(
    "s3",
    aws_access_key_id = S3_KEY,
    aws_secret_access_key = S3_SECRET
)
#bucket_name = 'text0detection'
bucket_upload = 'calacaschidas'
bucket_download = 'calacaschidasdown'
upload_folder = 'UpTest'

app_bbva = Flask(__name__)
Bootstrap(app_bbva)
app_bbva.jinja_env.filters['dateformat'] = dateformat
app_bbva.jinja_env.filters['gettype'] = gettype

@app_bbva.route('/')
def index():
    return render_template('home.html')

@app_bbva.route('/files', methods=['GET','POST'])
def files():
    s3_resource = boto3.resource('s3')
    my_bucket = s3_resource.Bucket(bucket_upload)
    summaries = my_bucket.objects.all()
    return render_template('files.html', my_bucket=my_bucket, files = summaries)

@app_bbva.route('/upload',methods=['POST'])
def upload():
    if request.method == 'POST':
        s3_resource = boto3.resource('s3')
        my_bucket = s3_resource.Bucket(bucket_upload)
        summaries = my_bucket.objects.all()
        for file in request.files.getlist("file[]"):
            print('name:'+str(file.filename)+'/ file:'+str(file))
            my_bucket.Object(os.path.join('DownTest',file.filename)).put(Body = file)

        return render_template('files.html', my_bucket=my_bucket, files = summaries)

@app_bbva.route('/tablas', methods=['GET','POST'])
def tablas():
    s3_resource = boto3.resource('s3')
    my_bucket = s3_resource.Bucket(bucket_upload)
    summaries = my_bucket.objects.all()
    return render_template('tablas.html',my_bucket=my_bucket, files = summaries)

@app_bbva.route('/set_ajax', methods=['POST'])
def set_ajax():
    if request.method == 'POST':

        files = boto3.client('s3').list_objects(Bucket=bucket_upload)['Contents']
        files =  [x['Key'] for x in files]
        calacas_chidas.modelo(files)
        results = []

        if os.path.exists('/home/notcelis/Escritorio/G.E.T/flaskS3/ETL.csv'):
            os.remove('/home/notcelis/Escritorio/G.E.T/flaskS3//ETL.csv')
        path = download('ETL.csv',bucket_upload)
        with open(path,newline='\n') as csv_file:
            data = csv.DictReader(csv_file)
            for row in data:
                results.append(dict(row))
            fieldnames = [key for key in results[0].keys()]
    return json.dumps(results)

@app_bbva.route('/delete',methods=['POST'])
def delte():
    if request.method == 'POST':
        s3_resource = boto3.resource('s3')
        my_bucket = s3_resource.Bucket(bucket_upload)
        summaries = my_bucket.objects.all()
        file = request.form['id']
        print('file',file)
        s3_resource.Object(bucket_upload,file).delete()
        return render_template('files.html', my_bucket=my_bucket, files = summaries)



def download(name,mybucket):
    bucket = mybucket
    bucket_files = boto3.client('s3').list_objects(Bucket=bucket)['Contents']
    bucket_files = [x['Key'] for x in bucket_files]
    try:
        bucket_file = name
        file_path = os.path.join('static/csv', bucket_file)
        if bucket_file not in os.listdir('static/csv'):
            boto3.client('s3').download_file(bucket, name, file_path)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code']=="404":
            print("doesn't exist")
        else:
            raise
    return file_path




if __name__ == '__main__':
    app_bbva.run(debug=True)