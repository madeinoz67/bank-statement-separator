// Version Selector JavaScript
document.addEventListener('DOMContentLoaded', function () {
    // Create version selector container
    const versionSelector = document.createElement('div');
    versionSelector.className = 'version-selector';

    // Create select element
    const select = document.createElement('select');
    select.id = 'version-select';
    select.setAttribute('aria-label', 'Documentation Version');

    // Add current version as default
    const currentVersion = getCurrentVersion();
    const defaultOption = document.createElement('option');
    defaultOption.value = '/';
    defaultOption.textContent = 'latest';
    if (currentVersion === 'latest' || !currentVersion) {
        defaultOption.selected = true;
    }
    select.appendChild(defaultOption);

    // Fetch available versions and populate selector
    fetchVersions().then(versions => {
        versions.forEach(version => {
            const option = document.createElement('option');
            option.value = `/${version}/`;
            option.textContent = version;

            // Mark current version as selected
            if (currentVersion === version) {
                option.selected = true;
            }

            select.appendChild(option);
        });
    });

    // Add change event listener
    select.addEventListener('change', function () {
        const selectedVersion = this.value;
        const baseUrl = 'https://madeinoz67.github.io/bank-statement-separator';
        window.location.href = baseUrl + selectedVersion;
    });

    versionSelector.appendChild(select);

    // Insert version selector into the header
    const header = document.querySelector('.md-header__inner');
    if (header) {
        // Try to find the header navigation area
        let insertPoint = header.querySelector('.md-header__option') ||
            header.querySelector('.md-header-nav') ||
            header.querySelector('.md-header__title');

        if (insertPoint) {
            // Insert as first child to avoid overlap with navigation
            insertPoint.insertBefore(versionSelector, insertPoint.firstChild);
        } else {
            // Fallback: create a wrapper and prepend to header
            const wrapper = document.createElement('div');
            wrapper.style.display = 'flex';
            wrapper.style.alignItems = 'center';
            wrapper.style.marginRight = '1rem';
            wrapper.appendChild(versionSelector);

            // Insert at the beginning of the header
            if (header.firstChild) {
                header.insertBefore(wrapper, header.firstChild);
            } else {
                header.appendChild(wrapper);
            }
        }
    } else {
        // Last resort: insert at top of body with fixed positioning
        console.warn('Could not find header, inserting version selector at top of page');
        versionSelector.style.position = 'fixed';
        versionSelector.style.top = '10px';
        versionSelector.style.right = '10px';
        versionSelector.style.zIndex = '1000';
        document.body.insertBefore(versionSelector, document.body.firstChild);
    }
});

function getCurrentVersion() {
    const path = window.location.pathname;
    // Handle version format v0.1.0
    const versionMatch = path.match(/^\/bank-statement-separator\/v(\d+\.\d+(?:\.\d+)?)\//);
    return versionMatch ? `v${versionMatch[1]}` : 'latest';
}

async function fetchVersions() {
    try {
        // In a real implementation, this would fetch from GitHub API
        // For now, we'll use a static list that gets updated by the CI/CD
        const response = await fetch('/bank-statement-separator/version-list.json');
        if (response.ok) {
            const data = await response.json();
            return data.versions || [];
        }
    } catch (error) {
        console.warn('Could not fetch versions:', error);
    }

    // Fallback: extract versions from current page
    return extractVersionsFromPage();
}

function extractVersionsFromPage() {
    // This is a fallback method to extract versions from the page
    // In practice, you'd want to maintain a versions.json file
    const versions = [];

    // Look for version links in navigation or footer
    const links = document.querySelectorAll('a[href*="/v"]');
    links.forEach(link => {
        const href = link.getAttribute('href');
        // Handle version format v0.1.0
        const versionMatch = href.match(/\/v(\d+\.\d+(?:\.\d+)?)\//);
        if (versionMatch && !versions.includes(`v${versionMatch[1]}`)) {
            versions.push(`v${versionMatch[1]}`);
        }
    });

    return versions.sort((a, b) => {
        // Sort versions in reverse order (newest first)
        const parseVersion = (v) => v.replace('v', '').split('.').map(Number);
        const aVer = parseVersion(a);
        const bVer = parseVersion(b);
        
        for (let i = 0; i < Math.max(aVer.length, bVer.length); i++) {
            const aPart = aVer[i] || 0;
            const bPart = bVer[i] || 0;
            if (aPart !== bPart) return bPart - aPart;
        }
        return 0;
    });
}
