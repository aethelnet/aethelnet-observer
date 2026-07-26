
import numpy as np
import networkx as nx

class TopologyEngine:
    """
    The Cartographer of the Market Galaxy.
    Converts raw correlation matrices into a structural graph (NetworkX).
    Calculates Centrality (Influence) and Minimum Spanning Trees (Structure).
    """
    def __init__(self):
        self.graph = nx.Graph()
        
    def update(self, correlation_matrix: np.ndarray, tickers: list, volumes: dict = None) -> dict:
        """
        Updates the internal graph topology based on new correlation data.
        Returns visualizable data: { centrality: {ticker: score}, edges: [{source, target, weight}] }
        """
        # 1. Reset Graph
        self.graph.clear()
        
        n = len(tickers)
        if correlation_matrix.shape != (n, n):
            return {}
            
        # 2. Build Graph (Thresholded)
        # We only keep strong links to avoid a hairball
        threshold = 0.5 
        
        edges = []

        # 3. Compute Mass (from Volumes)
        # Mass = log10(Volume + 1)
        masses = []
        if volumes is not None and len(volumes) == n:
            # Check if volume is list or dict
            if isinstance(volumes, dict):
                masses = [np.log10(max(1.0, float(volumes.get(t, 1.0)))) for t in tickers]
            elif isinstance(volumes, list):
                masses = [np.log10(max(1.0, float(v))) for v in volumes]
            else:
                 masses = [1.0] * n
        else:
            # Default Mass = 1.0 (if volume missing)
            masses = [1.0] * n

        # Normalize Masses (0 to 1 scale relative to max mass) to keep weights sane
        max_mass = max(masses) if masses else 1.0
        if max_mass > 0:
            masses = [m / max_mass for m in masses]

        for i in range(n):
            for j in range(i + 1, n):
                corr = correlation_matrix[i, j]
                # Base Weight = Absolute Correlation
                base_weight = abs(corr)
                
                # Gravitational Force = (Mass_A * Mass_B) * Correlation
                # We boost the link if both are heavy.
                gravity = base_weight * (masses[i] * masses[j])
                
                # Check Threshold (using gravity or base_weight? Base. We want strong correlations first.)
                if base_weight > threshold:
                    self.graph.add_edge(tickers[i], tickers[j], weight=gravity)
                    edges.append({
                        "source": tickers[i], 
                        "target": tickers[j], 
                        "weight": float(gravity),
                        "mass_source": float(masses[i]),
                        "mass_target": float(masses[j])
                    })
        
        # 3. Compute Centrality (Eigenvector or Degree)
        if len(self.graph.nodes) > 0:
            try:
                # Eigenvector centrality is good for finding "Influencers"
                if len(self.graph.nodes) > 2:
                    centrality = nx.eigenvector_centrality_numpy(self.graph, weight='weight')
                else:
                    centrality = nx.degree_centrality(self.graph)
            except:
                # Fallback to degree centrality if convergence fails
                centrality = nx.degree_centrality(self.graph)
        else:
            centrality = {t: 0 for t in tickers}
            
        # Normalize Centrality for Visualization (0 to 1)
        if centrality:
            max_c = max(centrality.values()) if centrality.values() else 1
            if max_c > 0:
                centrality = {k: v / max_c for k, v in centrality.items()}
                
        return {
            "centrality": centrality,
            "edges": edges
        }
