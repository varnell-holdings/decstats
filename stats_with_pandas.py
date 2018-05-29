from jinja2 import Environment, PackageLoader
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
# import matplotlib.pyplot as plt


def get_data():
    data = pd.read_csv('medical_data.csv')
    last_date = data['date'][len(data['date']) - 1]
    grouped_data = data.groupby('consultant').sum()
    grouped_data = data.groupby('consultant').count().sort_values('date', ascending=False)
    result = grouped_data['date']
    data = result.to_frame().iterrows()
    # graph = result.plot(
    #     kind='barh', title='Patients thru {}'.format(last_date))
    # ax = graph.get_figure()
    # ax.savefig('med_data.png')
    sns.set()
    result.plot.barh()
    plt.tight_layout()
    plt.savefig('med_data.png')
    return_data = []
    for doc, num in data:
        return_data.append((doc, str(num).split()[1]))
    return return_data, last_date


def make_medical_stats(data, last_date):
    """Render jinja2 template and write to file."""

    loader = PackageLoader('templates', '')
    env = Environment(loader=loader)
    template_name = 'med_stats_template.html'
    template = env.get_template(template_name)
    a = template.render(data=data, date=last_date)
    with open('medical_stats.html', 'w') as f:
        f.write(a)


if __name__ == '__main__':
    data, last_date = get_data()
    make_medical_stats(data, last_date)
