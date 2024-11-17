from decimal import Decimal
import os
import pandas as pd
import uuid
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import SignupForm, LoginForm, UploadFileForm
from .models import UserMetrics
import plotly.express as px
from django.contrib.auth import authenticate, login 
from django.contrib.auth import logout 

# Define path for uploaded files
UPLOAD_DIR = os.path.join(settings.MEDIA_ROOT, 'upload')

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def preprocess_data(file_path):
    df = pd.read_csv(file_path)
    
    # Convert 'Purchase Date' to datetime
    df['Purchase Date'] = pd.to_datetime(df['Purchase Date'], errors='coerce', dayfirst=True)
    
    # Drop duplicates
    df.drop_duplicates(inplace=True)
    
    # Fill missing values
    for col in df.select_dtypes(include=['number']).columns:
        df[col] = df[col].fillna(df[col].median())
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].fillna('Unknown')
    
    return df

def aggregate_data(df):
    df['Net Amount'] = df['Net Amount'].apply(lambda x: float(x) if isinstance(x, Decimal) else x)
    agegroup_summary = df.groupby('Age Group').agg(
        total_purchases=('CID', 'count'),
        total_revenue=('Net Amount', 'sum')
    ).reset_index()
    return agegroup_summary

def generate_plots(df, agegroup_summary):
    unique_id = str(uuid.uuid4())  # Generate a unique identifier for each plot session
    plot_dir = os.path.join(settings.MEDIA_ROOT, 'upload', 'plots')
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)
    
    # Plot Total Purchases by Age Group
    purchases_bar = agegroup_summary
    fig1 = px.bar(purchases_bar, x='total_purchases', y='Age Group', 
                  title='Total Purchases by Age Group', labels={'total_purchases': 'Purchases', 'Age Group': 'Age Group'})
    fig1_path = os.path.join(plot_dir, f'{unique_id}_purchases_bar.png')
    fig1.write_image(fig1_path)  # Save as PNG

    # Plot Total Revenue by Age Group
    revenue_bar = agegroup_summary
    fig2 = px.bar(revenue_bar, x='total_revenue', y='Age Group', 
                  title='Total Revenue by Age Group', labels={'total_revenue': 'Revenue', 'Age Group': 'Age Group'})
    fig2_path = os.path.join(plot_dir, f'{unique_id}_revenue_bar.png')
    fig2.write_image(fig2_path)  # Save as PNG

    # Plot Monthly Sales
    monthly_sales = df.groupby(df['Purchase Date'].dt.month)['Net Amount'].sum().reset_index()
    fig3 = px.line(monthly_sales, x='Purchase Date', y='Net Amount', 
                   title='Total Sales by Month', labels={'Purchase Date': 'Month', 'Net Amount': 'Sales'})
    fig3_path = os.path.join(plot_dir, f'{unique_id}_monthly_sales.png')
    fig3.write_image(fig3_path)  # Save as PNG

    # Plot Product Category Sales
    prod_cat_sales = df.groupby('Product Category')['Net Amount'].sum().reset_index()
    fig4 = px.bar(prod_cat_sales, x='Product Category', y='Net Amount', 
                  title='Total Sales by Product Category', labels={'Product Category': 'Product Category', 'Net Amount': 'Sales'})
    fig4_path = os.path.join(plot_dir, f'{unique_id}_prod_cat_sales.png')
    fig4.write_image(fig4_path)  # Save as PNG

    return {
    'purchases_bar': os.path.relpath(fig1_path, settings.MEDIA_ROOT),
    'revenue_bar': os.path.relpath(fig2_path, settings.MEDIA_ROOT),
    'monthly_sales_plot': os.path.relpath(fig3_path, settings.MEDIA_ROOT),
    'product_category_plot': os.path.relpath(fig4_path, settings.MEDIA_ROOT),
}
    
    
@login_required
def upload_file(request):
    if request.method == 'POST' and 'file' in request.FILES:
        uploaded_file = request.FILES['file']
        unique_filename = f"{uuid.uuid4()}{os.path.splitext(uploaded_file.name)[1]}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        # Save uploaded file
        with open(file_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        # Process the file
        df = preprocess_data(file_path)

        # Aggregate and generate insights
        agegroup_summary = aggregate_data(df)
        plot_paths = generate_plots(df, agegroup_summary)

        # Store metrics and visualizations in session
        request.session['metrics'] = {
            'total_sales': df['Net Amount'].sum(),
            'total_purchases': df['TID'].nunique(),
            'top_product': df.groupby('Product Category')['Net Amount'].sum().idxmax(),
            'top_location': df.groupby('Location')['Net Amount'].sum().idxmax(),
        }
        request.session['plot_paths'] = plot_paths
        request.session['agegroup_summary'] = agegroup_summary.to_dict(orient='records')

        # Redirect to the display page after upload
        return redirect('display_page')

    form = UploadFileForm()
    return render(request, 'visualizer/upload.html', {'form': form})



@login_required
def display_page(request):
    plot_paths = request.session.get('plot_paths', {})
    metrics = request.session.get('metrics', {})
    suggestions = [
        "Focus on Age Group and Product Category for insights on your top-selling demographics and products.",
        "Review the Monthly Sales graph to identify trends or seasonality in sales.",
        "The Total Revenue by Age Group can help you identify which groups are most profitable."
    ]

    # Ensure plot paths are prefixed with MEDIA_URL
    for key, path in plot_paths.items():
        plot_paths[key] = f"{settings.MEDIA_URL}{path}"

    return render(request, 'visualizer/display_images.html', {
        'plot_paths': plot_paths,
        'metrics': metrics,
        'suggestions': suggestions,
    })

    
    
def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'visualizer/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                form.add_error(None, 'Invalid username or password')
    else:
        form = LoginForm()
    return render(request, 'visualizer/login.html', {'form': form})

@login_required
def dashboard(request):
    # Just render the dashboard with the user details and upload form
    return render(request, 'visualizer/dashboard.html')

def logout_view(request):
    logout(request)
    return redirect('login')
