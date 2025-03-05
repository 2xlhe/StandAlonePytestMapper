import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px

from datetime import datetime
import tempfile


class DataPlotter:
    def __init__(self, test_data_base: type):
        self.execution_entity = test_data_base.execution_entity
        self.artifact_info = test_data_base.artifact_info
        self.tests = test_data_base.tests
        self.execution_time = test_data_base.execution_time
        self.failures = test_data_base.failures

        # Ensure types are correct
        assert isinstance(self.execution_entity, pd.DataFrame), "Execution Entity must be a df"
        assert isinstance(self.artifact_info, pd.DataFrame), "Artifact Info must be a df"
        assert isinstance(self.tests, pd.DataFrame), "Tests must be a df"
        assert isinstance(self.execution_time, pd.DataFrame), "Execution Time must be a df"
        assert isinstance(self.failures, pd.DataFrame), "Failures must be a df"

    def test_name_error_distribution_pie_chart(self):
        failures_df = self.failures

        # Chart needs only Test_Names and their frequency
        test_num_failures = failures_df.Test_Name.value_counts().to_dict()
        
        # Get names and values
        names = list(test_num_failures.keys())
        values = list(test_num_failures.values())

        # Create the pie chart
        fig = px.pie(
            names=names, 
            values=values, 
            title="Distribuição de falhas por teste",
            color_discrete_sequence=px.colors.sequential.RdBu,
        )

        fig.update_layout(
            margin=dict(l=20, r=20, t=40, b=20)  # Adjust margins if needed
        )

        # Make the pie chart circle bigger by adjusting the marker size
        fig.update_traces(
            marker=dict(line=dict(color='white', width=2)),  # Optional: Add a white border
            textposition='inside',  # Display text inside the slices
            textinfo='percent+label'  # Show percentage and label
        )
        fig.show()

    def plot_category_errors_bar(self):
        failures_df = self.failures.copy()
        # Chart needs only Test_Names and their frequency
        test_num_failures = failures_df.Test_Name.value_counts().to_dict()

        # PK = Test_Name:Name, Execution_DateTime
        categories_df = failures_df.merge(self.tests, 
                                how='inner', 
                                right_on=['Name', 'Execution_DateTime'], 
                                left_on=['Test_Name', 'Execution_DateTime'])

        # Creating a df With categories as each error
        categories_df = categories_df.groupby(by=['Category','Error']).size().unstack('Error').fillna(0).astype(int)

        # Plot the data
        fig = px.bar(categories_df, x=categories_df.index, y=categories_df.columns, barmode='stack', color_discrete_sequence=px.colors.sequential.RdBu)

        # Customize the plot
        fig.update_layout(
            title="Distribuição de erros por categoria",
            xaxis_title="Categoria",
            yaxis_title="Contagem Total"
        )

        # Show the plot
        fig.show()

    def categories_failures_passed_rate(self):
        # Group by status and category, then calculate value counts
        total_category = pd.DataFrame(self.tests).groupby(['Status', 'Category']).size().unstack().fillna(0).astype(int)

        # Calculate total tests per category
        total_category['TOTAL'] = total_category.sum(axis=1)

        # Calculate percentage for each status
        for status in total_category.columns:
            if status != 'TOTAL':
                total_category[f'{status}_PCT'] = (total_category[status] / total_category['TOTAL']) * 100

        # Prepare data for plotting
        plot_data = []
        for category in total_category.index:
            for status in total_category.columns:
                if status != 'TOTAL' and not status.endswith('_PCT'):
                    plot_data.append({
                        'Category': category,
                        'Status': status,
                        'Percentage': total_category.loc[category, f'{status}_PCT'] if f'{status}_PCT' in total_category.columns else 0,
                        'Real Value': total_category.loc[category, status]
                    })

        plot_df = pd.DataFrame(plot_data)

        # Create a stacked bar plot
        fig = px.bar(
            plot_df, 
            x="Category", 
            y="Percentage", 
            color="Status", 
            barmode='stack', 
            title="Proporção de testes por status",
            labels={'Percentage': 'Porcentagem'},
            text=plot_df["Real Value"].round(0).astype(int)  # Display real values on bars
        )

        # Adjust layout to display values inside bars
        fig.update_traces(texttemplate='%{text}', textposition='inside')
        fig.update_yaxes(title='Porcentagem')
        fig.update_xaxes(title='Categoria')

        # Display the plot
        fig.show()
