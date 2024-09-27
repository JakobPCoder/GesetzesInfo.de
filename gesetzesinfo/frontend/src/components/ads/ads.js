import React from 'react';
import GoogleAd from './google_ad';
import './ads.css';

const AD_CLIENT = process.env.ADSENSE_AD_CLIENT_ID;
const AD_SLOT_MOBILE = process.env.ADSENSE_AD_SLOT_MOBILE;
const AD_SLOT_DESKTOP = process.env.ADSENSE_AD_SLOT_DESKTOP;

function AdsMobile() {
    return (
        <div className="ads-container-mobile">
            <GoogleAd
                adClient={AD_CLIENT}
                adSlot={AD_SLOT_MOBILE}
                style={{ width: "100%", height: "200px" }}
            />
        </div>
    );
}

function AdsDesktop() {
    return (
        <div className="ads-container-desktop">
            <GoogleAd
                adClient={AD_CLIENT}
                adSlot={AD_SLOT_DESKTOP}
                style={{ width: "100%", height: "200px" }}
            />
        </div>
    );
}

export { AdsMobile, AdsDesktop };
