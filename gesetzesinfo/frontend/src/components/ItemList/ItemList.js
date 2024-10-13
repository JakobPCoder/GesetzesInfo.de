import React, { useEffect } from 'react';
import ListItem from './ListItem';
import './ItemList.css';

function ItemList({ items, error}) {

    useEffect(() => {
        // Re-render the list whenever the items prop changes
    }, [items]);

    return (
        <div className="item-list-container">
            <div className="list-header">
                <div className="header-id">ID</div>
                <div className="header-title">Title</div>
                <div className="header-score">Score</div>
            </div>
            
            {items.length > 0 ? (
                items.map(item => (
                    <ListItem
                        key={String(item.query_id) + String(item.id)}
                        id={item.id}
                        title={item.title}
                        text={item.text}
                        score={item.score}
                        query_id={item.query_id}
                        show_id={item.show_id}
                    />
                ))
            ) : (
                <div className="no-results">
                    {error ? error : "No results yet"}
                </div>
            )}
        </div>
    );
}

export default ItemList;
