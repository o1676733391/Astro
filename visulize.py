"""
Advanced 3D Astrological Visualization System
Fully 3D spatial mapping using varied radii and declination for an immersive web of aspects.
Dynamically loads natal chart data from houses.csv.
Uses Plotly's native legend grouping to act as interactive checkboxes.
"""

import math
import numpy as np
import plotly.graph_objects as go
import sys
import os

try:
    import pandas as pd
except ImportError:
    print("Please install pandas, numpy, and plotly: pip install pandas numpy plotly")
    sys.exit(1)

def spherical_to_cartesian(r, lon_deg, lat_deg):
    lon_rad = math.radians(lon_deg)
    lat_rad = math.radians(lat_deg)
    x = r * math.cos(lat_rad) * math.cos(lon_rad)
    y = r * math.cos(lat_rad) * math.sin(lon_rad)
    z = r * math.sin(lat_rad)
    return x, y, z

def create_zodiac_ring(radius=60, z=0):
    signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
             'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    traces = []
    
    theta = np.linspace(0, 360, 360)
    x = radius * np.cos(np.radians(theta))
    y = radius * np.sin(np.radians(theta))
    
    traces.append(go.Scatter3d(
        x=x, y=y, z=[z]*360,
        mode='lines',
        line=dict(color='rgba(255, 255, 255, 0.15)', width=2),
        name="Zodiac Boundary (Toggle)",
        legendgroup="Zodiac",
        showlegend=True,
        hoverinfo='none'
    ))

    for sign in signs:
        traces.append(go.Scatter3d(
            x=[0], y=[0], z=[z], # placeholder for sign text, handled differently if we want grouping
            mode='lines',
            line=dict(color='rgba(255, 255, 255, 0.1)', width=1),
            legendgroup="Zodiac",
            showlegend=False,
            hoverinfo='none'
        ))
        
    for i, sign in enumerate(signs):
        deg = i * 30
        mx = radius * math.cos(math.radians(deg))
        my = radius * math.sin(math.radians(deg))
        
        traces.append(go.Scatter3d(
            x=[0, mx], y=[0, my], z=[z, z],
            mode='lines',
            line=dict(color='rgba(255, 255, 255, 0.1)', width=1),
            legendgroup="Zodiac",
            showlegend=False,
            hoverinfo='none'
        ))
        
        lx = (radius + 4) * math.cos(math.radians(deg + 15))
        ly = (radius + 4) * math.sin(math.radians(deg + 15))
        traces.append(go.Scatter3d(
            x=[lx], y=[ly], z=[z],
            mode='text',
            text=[sign],
            textfont=dict(color='rgba(255, 255, 255, 0.4)', size=10),
            legendgroup="Zodiac",
            showlegend=False,
            hoverinfo='none'
        ))
        
    return traces

def get_midpoint(deg1, deg2):
    diff = (deg2 - deg1) % 360
    if diff > 180:
        diff -= 360
    mid = (deg1 + diff / 2) % 360
    return mid

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(script_dir, 'houses.csv')
    
    if not os.path.exists(csv_file):
        print(f"Error: Could not find {csv_file}")
        sys.exit(1)
    
    if os.path.getsize(csv_file) == 0:
        print(f"Error: {csv_file} is empty (0 bytes). Please save the file in your editor.")
        sys.exit(1)
        
    try:
        df = pd.read_csv(csv_file)
        df.columns = df.columns.str.strip()
    except pd.errors.EmptyDataError:
        print(f"Error: {csv_file} contains no valid data columns to parse.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        sys.exit(1)
    
    df_houses = df[df['Category'] == 'House']
    df_planets = df[(df['Category'] == 'Planet') | (df['Category'] == 'Node')]
    df_moons = df[df['Category'] == 'Moon']
    
    fig = go.Figure()

    # 1. Background Frame
    for trace in create_zodiac_ring(radius=60, z=0):
        fig.add_trace(trace)

    # 2. House Logic
    first_house = True
    for _, row in df_houses.iterrows():
        name = row['Object']
        deg = row['Absolute_Degrees_360']
        
        is_anchor = any(a in name for a in ['Ascendant', 'Descendant', 'Midheaven', 'IC'])
        line_color = 'rgba(255, 255, 255, 0.6)' if is_anchor else 'rgba(255, 255, 255, 0.2)'
        line_width = 2 if is_anchor else 1
        
        x = 60 * math.cos(math.radians(deg))
        y = 60 * math.sin(math.radians(deg))
        
        fig.add_trace(go.Scatter3d(
            x=[0, x], y=[0, y], z=[0, 0],
            mode='lines+text',
            line=dict(color=line_color, width=line_width, dash='dash' if is_anchor else 'dot'),
            text=[name.split()[0]] if is_anchor else [None],
            textposition='top center',
            name="House Cusps (Toggle)" if first_house else name,
            legendgroup="Houses",
            showlegend=first_house,
            hoverinfo='name'
        ))
        first_house = False

    # 3. Planet Data
    planet_meta = {
        'Sun':        {'r': 21.0, 'size': 20.0, 'lat': 5,   'ray': 'Ray 2', 'color': '#ffcc00'},
        'Moon':       {'r': 3.5,  'size': 0.27, 'lat': -15, 'ray': 'Ray 4', 'color': '#d3d3d3'},
        'Mercury':    {'r': 14.0, 'size': 0.38, 'lat': -5,  'ray': 'Ray 4', 'color': '#b0b0b0'},
        'Venus':      {'r': 18.0, 'size': 0.95, 'lat': 10,  'ray': 'Ray 5', 'color': '#f5b042'},
        'Mars':       {'r': 24.0, 'size': 0.53, 'lat': -10, 'ray': 'Ray 6', 'color': '#f54242'},
        'Jupiter':    {'r': 34.0, 'size': 11.2, 'lat': 8,   'ray': 'Ray 2', 'color': '#d39c7e'},
        'Saturn':     {'r': 40.0, 'size': 9.45, 'lat': -8,  'ray': 'Ray 3', 'color': '#ead6b8'},
        'Uranus':     {'r': 46.0, 'size': 4.0,  'lat': 12,  'ray': 'Ray 7', 'color': '#4b70dd'},
        'Neptune':    {'r': 50.0, 'size': 3.88, 'lat': -12, 'ray': 'Ray 6', 'color': '#274687'},
        'Pluto':      {'r': 52.0, 'size': 0.18, 'lat': 18,  'ray': 'Ray 1', 'color': '#ffffff'},
        'North Node': {'r': 4.0,  'size': 0.5,  'lat': 0,   'ray': 'Karmic', 'color': '#aaaaaa'}
    }

    coords = {}
    first_planet = True
    for _, row in df_planets.iterrows():
        name = row['Object']
        deg = row['Absolute_Degrees_360']
        retro = " (R)" if row['Retrograde'] == 'Yes' else ""
        
        meta = planet_meta.get(name, {'r': 20, 'size': 1.0, 'lat': 0, 'ray': 'Unknown', 'color': '#ffffff'})
        x, y, z = spherical_to_cartesian(meta['r'], deg, meta['lat'])
        coords[name] = (x, y, z, deg)
        
        visual_size = math.sqrt(meta['size']) * 2.5 + 2
        
        fig.add_trace(go.Scatter3d(
            x=[x], y=[y], z=[z],
            mode='markers+text',
            marker=dict(size=visual_size, color=meta['color'], symbol='circle', line=dict(color='white', width=1)),
            text=[name + retro],
            textposition='top center',
            name="Planets & Moons (Toggle)" if first_planet else name,
            legendgroup="Planets",
            showlegend=first_planet,
            hoverinfo='text',
            hovertext=f"{name}{retro}<br>Lon: {deg:.2f}°<br>Log Dist: {meta['r']}<br>Size (Earth=1): {meta['size']}"
        ))
        
        fig.add_trace(go.Scatter3d(
            x=[x, x], y=[y, y], z=[z, 0],
            mode='lines',
            line=dict(color='rgba(255, 255, 255, 0.2)', width=1, dash='dot'),
            legendgroup="Planets",
            showlegend=False, hoverinfo='none'
        ))
        first_planet = False

    # 4. Aspect Pattern Theory (Lines between planets)
    first_aspect = True
    def draw_aspect(p1, p2, color, weight, name_label):
        nonlocal first_aspect
        if p1 not in coords or p2 not in coords: return
        px1, py1, pz1, _ = coords[p1]
        px2, py2, pz2, _ = coords[p2]
        fig.add_trace(go.Scatter3d(
            x=[px1, px2], y=[py1, py2], z=[pz1, pz2],
            mode='lines',
            line=dict(color=color, width=weight),
            name="Aspect Lines (Toggle)" if first_aspect else name_label,
            legendgroup="Aspects",
            showlegend=first_aspect,
            hoverinfo='name',
            hovertext=name_label
        ))
        first_aspect = False

    draw_aspect('Uranus', 'Jupiter', 'rgba(255, 0, 0, 0.8)', 4, 'T-Square: Uranus Opp Jupiter')
    draw_aspect('Sun', 'Uranus', 'rgba(255, 0, 0, 0.8)', 4, 'T-Square: Sun Sq Uranus')
    draw_aspect('Sun', 'Jupiter', 'rgba(255, 0, 0, 0.8)', 4, 'T-Square: Sun Sq Jupiter')

    draw_aspect('Venus', 'Saturn', 'rgba(0, 255, 100, 0.6)', 3, 'Trine A: Venus-Saturn')
    draw_aspect('Saturn', 'Uranus', 'rgba(0, 255, 100, 1.0)', 6, 'Trine A/B: Saturn-Uranus (38.82)')
    draw_aspect('Uranus', 'Venus', 'rgba(0, 255, 100, 0.6)', 3, 'Trine A: Uranus-Venus')
    
    draw_aspect('Mars', 'Saturn', 'rgba(0, 200, 255, 0.6)', 3, 'Trine B: Mars-Saturn')
    draw_aspect('Uranus', 'Mars', 'rgba(0, 200, 255, 0.6)', 3, 'Trine B: Uranus-Mars')

    draw_aspect('Jupiter', 'Pluto', 'rgba(255, 255, 255, 1.0)', 8, 'Jupiter Trine Pluto (50.22)')

    # 5. Midpoint Theory
    if 'Neptune' in coords and 'North Node' in coords:
        nx, ny, nz, ndeg = coords['Neptune']
        nnx, nny, nnz, nndeg = coords['North Node']
        
        mx, my, mz = (nx + nnx) / 2, (ny + nny) / 2, (nz + nnz) / 2
        mid_deg = get_midpoint(ndeg, nndeg)
        
        fig.add_trace(go.Scatter3d(
            x=[mx], y=[my], z=[mz],
            mode='markers+text',
            marker=dict(size=4, color='yellow', symbol='diamond'),
            text=['Neptune/NN Midpoint'],
            textposition='bottom center',
            name='Midpoints (Toggle)',
            legendgroup="Midpoints",
            showlegend=True,
            hoverinfo='name'
        ))
        
        fig.add_trace(go.Scatter3d(
            x=[nx, mx, nnx], y=[ny, my, nny], z=[nz, mz, nnz],
            mode='lines',
            line=dict(color='rgba(255, 255, 0, 0.3)', width=2, dash='dot'),
            legendgroup="Midpoints",
            showlegend=False, hoverinfo='none'
        ))

    # 6. Overlay Theory (Planetcentric Moons)
    for _, row in df_moons.iterrows():
        name = row['Object']
        deg = row['Absolute_Degrees_360']
        is_planetcentric = "Planetcentric" in name
        
        if is_planetcentric:
            x, y, _ = spherical_to_cartesian(30, deg, 0)
            z = 25
            color = '#ffccff'
        else:
            x, y, z = spherical_to_cartesian(45, deg, 5)
            color = '#ff88cc'
            
        fig.add_trace(go.Scatter3d(
            x=[x], y=[y], z=[z],
            mode='markers+text',
            marker=dict(size=4, color=color),
            text=[name],
            textposition='top center',
            name=name,
            legendgroup="Planets", # Bundle moons with planets
            showlegend=False,
            hoverinfo='text',
            hovertext=f"{name}<br>Lon: {deg:.2f}°"
        ))

        fig.add_trace(go.Scatter3d(
            x=[x, x], y=[y, y], z=[z, 0],
            mode='lines',
            line=dict(color=color, width=2, dash='dot'),
            legendgroup="Planets",
            showlegend=False, hoverinfo='none'
        ))

    # Earth at Origin
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[0],
        mode='markers+text',
        marker=dict(size=math.sqrt(1.0) * 2.5 + 2, color='#2b82c9'), 
        text=['Earth'],
        name='Earth',
        legendgroup="Planets",
        showlegend=False,
        hoverinfo='text',
        hovertext='Earth<br>Size (Earth=1): 1.0'
    ))

    fig.update_layout(
        title="Immersive 3D Astrological Energy Web",
        # Enable the interactive checkbox legend
        showlegend=True,
        legend=dict(
            title="Interactive Filters (Click to Check/Uncheck)",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor='rgba(30, 30, 30, 0.8)',
            font=dict(color='white')
        ),
        scene=dict(
            xaxis=dict(showbackground=False, showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showbackground=False, showgrid=False, zeroline=False, showticklabels=False),
            zaxis=dict(showbackground=False, showgrid=False, zeroline=False, showticklabels=False),
            bgcolor='rgb(5, 5, 12)',
            aspectmode='cube'
        ),
        paper_bgcolor='rgb(5, 5, 12)',
        font=dict(color='white'),
        margin=dict(l=0, r=0, b=0, t=50)
    )

    # ---------------------------------------------------------
    # VERCEL DEPLOYMENT EXPORT
    # ---------------------------------------------------------
    html_output = os.path.join(script_dir, "index.html")
    print(f"Generating static web build at: {html_output}")
    # Export the entire interactive chart to a standalone HTML file. 
    # Using 'cdn' keeps the file size small by loading the rendering engine from the cloud.
    fig.write_html(html_output, include_plotlyjs="cdn", full_html=True)
    
    # Inject notification script for 3-minute viewing
    with open(html_output, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Add custom JavaScript for 3-minute notification
    notification_script = """
    <script>
    // Initialize 3-minute viewing notification
    (function() {
        const NOTIFICATION_DELAY = 3 * 60 * 1000; // 3 minutes in milliseconds
        let notificationShown = false;
        
        // Show notification after 3 minutes
        setTimeout(function() {
            if (!notificationShown) {
                notificationShown = true;
                
                // Create custom popup
                const popup = document.createElement('div');
                popup.id = 'viewing-notification';
                popup.style.cssText = `
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px 40px;
                    border-radius: 15px;
                    font-size: 24px;
                    font-weight: bold;
                    text-align: center;
                    z-index: 10000;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
                    animation: slideIn 0.5s ease-out;
                    font-family: 'Arial', sans-serif;
                `;
                popup.textContent = 'Caught it, you digging me! :>';
                
                document.body.appendChild(popup);
                
                // Add animation to body
                const style = document.createElement('style');
                style.textContent = `
                    @keyframes slideIn {
                        from {
                            opacity: 0;
                            transform: translate(-50%, -60%);
                        }
                        to {
                            opacity: 1;
                            transform: translate(-50%, -50%);
                        }
                    }
                    
                    @keyframes fadeOut {
                        from {
                            opacity: 1;
                            transform: translate(-50%, -50%);
                        }
                        to {
                            opacity: 0;
                            transform: translate(-50%, -40%);
                        }
                    }
                `;
                document.head.appendChild(style);
                
                // Auto-remove popup after 5 seconds
                setTimeout(function() {
                    popup.style.animation = 'fadeOut 0.5s ease-in forwards';
                    setTimeout(function() {
                        popup.remove();
                    }, 500);
                }, 5000);
            }
        }, NOTIFICATION_DELAY);
    })();
    </script>
    """
    
    # Insert the script before closing body tag
    html_content = html_content.replace('</body>', notification_script + '\n</body>')
    
    with open(html_output, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("Build complete! Drag this project folder into Vercel to deploy.")

    # Also open locally for immediate verification
    fig.show()

if __name__ == "__main__":
    main()
