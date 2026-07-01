import { graphConnect, sugiyama } from 'd3-dag';

function test() {
  const edges = [
    ['A', 'B'],
    ['C', 'D'] // Disconnected!
  ];
  
  try {
    const createDag = graphConnect()
    const dag = createDag(edges)
    const layout = sugiyama()
    layout(dag)
    
    for (const node of dag.nodes()) {
      console.log("DAG Node:", node.data, node.x, node.y)
    }
  } catch (err) {
    console.error("DAG Layout failed:", err)
  }
}

test()
