import React from 'react';
import ListItem from './ListItem';
import './ItemList.css';

function ItemList({ items, error, query}) {
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
                        key={item.id}
                        id={item.id}
                        title={item.title}
                        text={item.text}
                        query={query}
                        score={item.score}
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
