import { graphConnect, sugiyama } from 'd3-dag';

const edges = [
  ['a', 'b'],
  ['b', 'c']
];

try {
  const createDag = graphConnect();
  const dag = createDag(edges);
  const layout = sugiyama();
  layout(dag);
  
  for (const node of dag.nodes()) {
    console.log("Node:", node.data, node.x, node.y);
  }
} catch (e) {
  console.error("Error:", e);
}
