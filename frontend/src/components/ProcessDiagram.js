import React, { useCallback, useMemo } from 'react';
import ReactFlow, {
    Controls,
    Background,
    applyNodeChanges,
    applyEdgeChanges,
    addEdge,
} from 'reactflow';
import 'reactflow/dist/style.css';

// Simple layouting (can be improved significantly)
function getLayoutedElements(tasks) {
    const nodes = [];
    const edges = [];
    const initialX = 100;
    const initialY = 50;
    const yDistance = 100;

    tasks.forEach((task, index) => {
        nodes.push({
            id: task.id.toString(),
            data: { label: `(${task.actor_type}) ${task.action}` },
            position: { x: initialX, y: initialY + index * yDistance },
            // You can add custom styling based on actor_type here
            style: { background: task.actor_type === 'human' ? '#ffcccb' : '#add8e6', padding: 10 },

        });

        if (index > 0) {
            edges.push({
                id: `e${tasks[index - 1].id}-${task.id}`,
                source: tasks[index - 1].id.toString(),
                target: task.id.toString(),
                animated: false, // Set true for animated edges if desired
            });
        }
    });

    return { nodes, edges };
}


function ProcessDiagram({ tasks }) {
    // Use useMemo to prevent recalculating layout on every render unless tasks change
    const { nodes: layoutedNodes, edges: layoutedEdges } = useMemo(() => getLayoutedElements(tasks || []), [tasks]);

    // State for nodes and edges (React Flow needs state)
    const [nodes, setNodes] = React.useState(layoutedNodes);
    const [edges, setEdges] = React.useState(layoutedEdges);

    // Update state if layout changes (e.g., if tasks prop updates)
    React.useEffect(() => {
        setNodes(layoutedNodes);
        setEdges(layoutedEdges);
    }, [layoutedNodes, layoutedEdges]);


    const onNodesChange = useCallback(
        (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
        [setNodes]
    );
    const onEdgesChange = useCallback(
        (changes) => setEdges((eds) => applyEdgeChanges(changes, eds)),
        [setEdges]
    );
    // const onConnect = useCallback( // Usually not needed for display-only diagrams
    //     (connection) => setEdges((eds) => addEdge(connection, eds)),
    //     [setEdges]
    // );

    if (!tasks || tasks.length === 0) {
        return <div>No process tasks to display.</div>;
    }

    return (
        <div style={{ height: '400px', border: '1px solid #ccc', marginBottom: '20px' }}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                // onConnect={onConnect} // Enable if connections needed
                fitView // Zooms/pans to fit the calculated nodes
                attributionPosition="top-right"
            >
                <Controls />
                <Background />
            </ReactFlow>
        </div>
    );
}

export default ProcessDiagram;