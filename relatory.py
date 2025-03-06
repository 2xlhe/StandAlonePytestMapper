
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, ListFlowable, ListItem, Spacer, Image
from datetime import datetime

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
from dataPlotter import DataPlotter

class PdfMaker:
    def __init__(self, test_data):
        
        self.execution_entity = test_data.execution_entity
        self.tests = test_data.tests
        self.execution_time = test_data.execution_time
        self.failures = test_data.failures
        #self.artifact_info = test_data_base.artifact_info
        self.plotter = DataPlotter(test_data)

        # Ensure types are correct
        assert isinstance(self.execution_entity, pd.DataFrame), "Execution Entity must be a df"
        assert isinstance(self.tests, pd.DataFrame), "Tests must be a df"
        assert isinstance(self.execution_time, pd.DataFrame), "Execution Time must be a df"
        assert isinstance(self.failures, pd.DataFrame), "Failures must be a df"
        #assert isinstance(self.artifact_info, pd.DataFrame), "Artifact Info must be a df"


        styles = getSampleStyleSheet()
        self.styles = {
            'heading1': styles['Heading1'],
            'normal': styles['Normal'],
            'bold': ParagraphStyle(
                name="Bold",
                parent=styles['Normal'],
                fontName="Helvetica-Bold",
                fontSize=12
            )
        }

        # Define dimensions
        self.dim = {
            'width': A4[0],
            'height': A4[1],
            'margin': 0.1 * A4[0],  # Use A4[0] directly to avoid circular dependency
        }

    def __get_time__(self, merged_rows, metric):
        # Create a dict of the total time of each category summing each test time it contains
        time = pd.Series(dict(map(lambda t, x: (x, merged_rows.loc[merged_rows['Execution_name'] == t, metric].sum()), self.tests['Name'].unique(), self.tests['Name'].unique())))
    
        return time
    
    def create_pdf(self):

        # Create PDF with margins
        doc = SimpleDocTemplate("report_v0.pdf", pagesize=A4,
                                leftMargin=self.dim['margin'], rightMargin=self.dim['margin'], topMargin=0.1*self.dim['height'], bottomMargin=0.1*self.dim['height'])

        # Create the story (content) for the PDF
        story = []

        # Add title with fields
        story.extend(self.create_title())
        story.extend(self.create_execution_summary())
        story.extend(self.create_detailed_results())
        story.extend(self.create_errors_summary())
        story.extend(self.create_graphs())

        # Build PDF
        doc.build(story)

    def create_title(self):
        # Initialize the story list
        story = []

        # Get current date and time
        agora = datetime.now() 
        horario_dia = agora.strftime("%d/%m/%Y %H:%M:%S")

        # Create the title
        title_text = "Sumário de Resultados dos Testes"
        title_paragraph = Paragraph(f"<b>{title_text}</b>", self.styles['heading1'])


        # Add title and date to the story as separate elements
        story.append(title_paragraph)

        # Create the formatted text for the execution date, system version, and environment
        execution_paragraph = Paragraph(f"Data da Execução: {self.execution_entity.Execution_Datetime}", self.styles['normal'])
        version_paragraph = Paragraph("Versão do Sistema: ", self.styles['normal'])
        environment_paragraph = Paragraph("Ambiente: ", self.styles['normal'])

        # Add other paragraphs to the story
        story.append(execution_paragraph)
        story.append(Spacer(1, 6))  # Spacer between execution and version
        story.append(version_paragraph)
        story.append(Spacer(1, 6))  # Spacer between version and environment
        story.append(environment_paragraph)

        story.append(Spacer(1, 18))  # Add space at the end

        # Return the complete story
        return story

    def create_execution_summary(self):
        story = []
        story.append(Paragraph("Resumo Geral", self.styles['bold']))
        story.append(Spacer(1, 6))

        success_rate = self.tests['Status'].value_counts('Status').get('PASSED') * 100

        # Criando a lista de resumo corretamente
        summary_data = {
            'Total de Testes:': self.tests.index.size,
            'Testes Bem-Sucedidos:': self.tests['Status'].value_counts().get('PASSED', 0),
            'Testes com Falha:': self.tests['Status'].value_counts().get('PASSED', 0),
            'Taxa de Sucessos/Falha:': f"{success_rate}%",  # Round to 2 decimal places
            #'Tempo Mínimo de Execução:': f"{self.metrics_df['min_test_time'].min():.2f} s",
            #'Tempo Médio de Execução:': f"{self.metrics_df['avg_test_time'].mean():.2f} s",
            #'Duração Total dos Testes:': f"{self.metrics_df['total_duration'].sum():.2f} s"
        }

        # Criando a lista com bullet points
        bullet_points = [
            ListItem(Paragraph(f"<b>{key}</b> {value}", self.styles['normal']), leftIndent=20, spaceAfter=6)
            for key, value in summary_data.items()
        ]

        # Criando o ListFlowable
        list_flowable = ListFlowable(bullet_points, bulletType='bullet', leftIndent=20)

        # Adicionando ao relatório
        story.append(list_flowable)
        story.append(Spacer(1, 24))

        return story

    def create_detailed_results(self):
        story = []
        story.append(Paragraph("Detalhamento dos Testes", self.styles['bold']))
        story.append(Spacer(1, 12))
        
        # Number of passed and failed tests by Test_Name and Category
        passed_tests_df = self.tests.copy().groupby(['Name', 'Status']).size().unstack().fillna(0).astype(int)
        passed_tests_df.columns = ['Falhas', 'Acertos']

        # Retrieve the tests with their times_metrics
        time_metric_df = pd.merge(
                self.execution_time,
                self.tests[['Name', 'Execution_Datetime']],
                left_on=['Execution_name', 'Execution_Datetime'],
                right_on=['Name', 'Execution_Datetime'],
                how='inner'
        )
        
        avg_time = self.__get_time__(time_metric_df, 'Avg_Time')
        min_time = self.__get_time__(time_metric_df, 'Min_Time')
        total_time = self.__get_time__(time_metric_df, 'Total_Time')

        time_df = pd.DataFrame([avg_time,min_time,total_time]).T.reset_index()
        time_df.columns = ['Teste','Tempo médio', 'Tempo Mínimo', 'Tempo Total']
        
        time_metric_df = pd.merge(time_df,passed_tests_df,right_on=['Name'],left_on=['Teste'], how='inner')
        time_metric_df['Número de Testagens'] = time_metric_df['Falhas'] + time_metric_df['Acertos']


        # Prepare the detailed data for the table
        detailed_tests_data = [[Paragraph(str(value), self.styles['normal']) for value in time_metric_df.columns.tolist()]]  # Add header
        detailed_tests_data.extend(
            [[Paragraph(str(value), self.styles['normal']) for value in row] for row in time_metric_df.values.tolist()]
        )

        # Calculate available width after applying margins
        available_width = self.dim['width'] - 2 * self.dim['margin']  

        # Define column proportions
        proportions = [0.3, 0.15, 0.15, 0.15, 0.2, 0.15] 

        total_proportion = sum(proportions)
        if total_proportion > 1:
            proportions = [p / total_proportion for p in proportions]  

        # Calculate column widths based on width
        col_widths = [available_width * p for p in proportions]

        # Create the table
        detailed_table = Table(detailed_tests_data, colWidths=col_widths)
        detailed_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                            ('GRID', (0, 0), (-1, -1), 0.5, colors.black)]))
        story.append(detailed_table)
        story.append(Spacer(1, 24))

        return story

    def create_errors_summary(self):
        """
        Creates a summary of errors in a PDF document.

        :param df: DataFrame containing error data.
        :param normal_style: Style for normal text.
        :param bold_style: Style for bold text.
        :param width: Width of the page.
        :param margin: Margin size.
        :return: A list of elements to be added to the PDF.
        """
        story = []
        story.append(Paragraph("Resumo dos Erros", self.styles['bold']))
        story.append(Spacer(1, 12))

        # Create a copy of the DataFrame and reset the index
        categories_df = self.failures.merge(self.tests, 
                                how='inner', 
                                right_on=['Name', 'Execution_Datetime'], 
                                left_on=['Test_Name', 'Execution_Datetime'])
        
        categories_df = categories_df[['Test_Name', 'Category', 'Error', 'Details', 'Execution_Datetime']]
        categories_df.columns = [
            'Nome do teste',
            'Categoria',
            'Error',
            'Detalhes do erro',
            'Momento de execução',
        ]

        # Prepare the detailed data for the table
        detailed_tests_data = [[Paragraph(str(value), self.styles['normal']) for value in categories_df.columns.tolist()]] 
        detailed_tests_data.extend(
            [[Paragraph(str(value), self.styles['normal']) for value in row] for row in categories_df.values.tolist()]
        )

        # Calculate available width after applying margins
        available_width = self.dim['width'] - 2 * self.dim['margin']  
        proportions = [0.3, 0.15, 0.15, 0.15, 0.2, 0.1]  

        # Calculate column widths based on the available width
        col_widths = [available_width * p for p in proportions]

        # Create the table
        detailed_table = Table(detailed_tests_data, colWidths=col_widths)
        detailed_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  
        ]))
        story.append(detailed_table)
        story.append(Spacer(1, 24))

        return story

    def create_graphs(self):
        img_width = 500
        img_height = 250

        graph_files = {'error_distribution_pie':self.plotter.test_name_error_distribution_pie_chart(), 
                       'category_errors_bar': self.plotter.plot_category_errors_bar(),
                       'failures_passed_rate': self.plotter.categories_failures_passed_rate(),
                       }
        
        story = []
        story.append(Spacer(1, 12))

        # Add a title to the PDF
        story.append(Paragraph("Visualização de dados", self.styles['bold']))
        story.append(Spacer(1, 12))

        # Add the bar chart and aligning
        category_img = Image(graph_files['category_errors_bar'], width=img_width, height=img_height)
        category_img.hAlign = 'CENTER'

        # Add the pie chart and aligning
        error_dist_image = Image(graph_files['error_distribution_pie'], width=500, height=250)
        error_dist_image.hAlign = 'CENTER'
        
        # Add the pass/fail rate bar chart and aligning
        failure_passed_img = Image(graph_files['failures_passed_rate'], width=500, height=250)
        failure_passed_img.hAlign = 'CENTER'

        # Appending graphs to pdf
        story.append(category_img) 
        story.append(Spacer(1, 24))
        story.append(error_dist_image)  
        story.append(Spacer(1, 24))
        story.append(failure_passed_img)  
        story.append(Spacer(1, 24))

        return story

