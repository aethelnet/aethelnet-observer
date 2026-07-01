import { graphConnect, sugiyama } from 'd3-dag';

const edges = [
  ["A", "B"],
  ["B", "C"],
  ["A", "C"]
];

const createDag = graphConnect();
const dag = createDag(edges);

const layout = sugiyama();
layout(dag);

for (const node of dag.nodes()) {
  console.log(node.id, node.data, node.x, node.y);
}
