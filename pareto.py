"""Interactive Pareto visualization for HEEDS feasible-design CSV exports.

Install: pip install pandas plotly
Run: py pareto.py <path-to-csv> --log-y
     py pareto.py Opt_L400.csv <path-to-csv-1> <path-to-csv-2> --log-y
"""
import argparse
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.colors import qualitative

X = 'mass_kg'
Y = 'deflection_mm'


def read_heeds_csv(path):
    # HEEDS may prepend a one-cell title line before the CSV column names.
    with open(path, encoding='utf-8-sig') as f:
        first = f.readline().strip()
    skiprows = 0 if (X in first and Y in first) else 1
    df = pd.read_csv(path, skiprows=skiprows, sep=None, engine='python', skipinitialspace=True)
    df.columns = df.columns.str.strip()
    if X not in df or Y not in df:
        raise ValueError(f'{path}: expected columns {X} and {Y}; found {list(df.columns)}')
    df[X] = pd.to_numeric(df[X], errors='coerce')
    df[Y] = pd.to_numeric(df[Y], errors='coerce')
    df = df.dropna(subset=[X, Y]).copy()
    return df


def pareto_mask(df):
    """Non-dominated for minimizing X and Y. Equal objective pairs are retained."""
    ordered = df.sort_values([X, Y], kind='mergesort')
    # At each mass, minimum deflection among strictly lighter masses.
    # Straightforward vectorized sweep, including ties correctly.
    selected = []
    best_y_lighter = float('inf')
    for mass, group in ordered.groupby(X, sort=True):
        min_y_this_mass = group[Y].min()
        selected.extend(group.index[(group[Y] == min_y_this_mass) & (group[Y] < best_y_lighter)].tolist())
        best_y_lighter = min(best_y_lighter, min_y_this_mass)
    return df.index.isin(selected)


def main():
    parser = argparse.ArgumentParser(description='Interactive HEEDS Pareto chart from feasible CSV files')
    parser.add_argument('csv', nargs='+', type=Path, help='One or more feasible-only HEEDS CSV exports')
    parser.add_argument('--output', type=Path, default=Path('HEEDS_Pareto_interactive.html'))
    parser.add_argument('--log-y', action='store_true', help='Logarithmic deflection axis')
    parser.add_argument('--hide-all', action='store_true', help='Show only Pareto points')
    args = parser.parse_args()

    fig = go.Figure()
    palette = qualitative.Plotly
    for k, path in enumerate(args.csv):
        df = read_heeds_csv(path)
        # This script assumes the input has ALREADY been filtered to feasible designs.
        pareto = df.loc[pareto_mask(df)].sort_values(X).copy()
        label = path.stem.replace('_feasible', '').replace(' Design Table', '')
        pareto.to_csv(path.with_name(path.stem + '_pareto.csv'), index=False)

        # Add missing optional columns so all HEEDS variants work.
        id_col = next((c for c in ['Eval #', 'Design ID', 'Design', 'ID'] if c in df.columns), None)
        for frame in (df, pareto):
            frame['__id'] = frame[id_col].astype(str) if id_col else frame.index.astype(str)
            for col in ['b', 'h', 'L', 'length_mm', 'sigma_max_MPa']:
                if col not in frame:
                    frame[col] = '—'

        def custom(frame):
            return frame[['__id', 'b', 'h', 'L', 'sigma_max_MPa']].astype(str).to_numpy()

        hover = ('<b>Eval / Design ID: %{customdata[0]}</b><br>'
                 'Masse: %{x:.5g} kg<br>Durchbiegung: %{y:.5g} mm<br>'
                 'b: %{customdata[1]} mm<br>h: %{customdata[2]} mm<br>'
                 'L: %{customdata[3]} mm<br>σmax: %{customdata[4]} MPa<extra>%{fullData.name}</extra>')
        if not args.hide_all:
            fig.add_trace(go.Scattergl(
                x=df[X], y=df[Y], mode='markers', name=f'{label} · alle feasible',
                customdata=custom(df), hovertemplate=hover,
                marker=dict(size=5, color=palette[k % len(palette)], opacity=0.16),
                legendgroup=label, showlegend=True,
            ))
        fig.add_trace(go.Scatter(
            x=pareto[X], y=pareto[Y], mode='markers+lines',
            name=f'{label} · Pareto ({len(pareto)})',
            customdata=custom(pareto), hovertemplate=hover,
            marker=dict(size=8, color=palette[k % len(palette)], line=dict(width=1, color='white')),
            line=dict(width=1.8, color=palette[k % len(palette)]),
            legendgroup=label,
        ))
        print(f'{label}: feasible={len(df)}, Pareto={len(pareto)}; exported {path.stem}_pareto.csv')

    fig.update_layout(
        title='HEEDS NSGA-III — Pareto-Fronten (zulässige Lösungen)',
        xaxis_title='Masse [kg]', yaxis_title='Maximale Durchbiegung [mm]',
        template='plotly_white', hovermode='closest',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, x=0),
        margin=dict(l=70, r=30, t=115, b=70), height=720,
    )
    if args.log_y:
        fig.update_yaxes(type='log')
    fig.write_html(args.output, include_plotlyjs=True, full_html=True)
    print(f'Interactive chart: {args.output.resolve()}')


if __name__ == '__main__':
    main()
