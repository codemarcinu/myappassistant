import { configureAxe } from 'jest-axe';

// Configure axe-core for accessibility testing
configureAxe({
  rules: {
    // Disable rules that are not relevant for our testing environment
    'color-contrast': { enabled: true },
    'document-title': { enabled: true },
    'html-has-lang': { enabled: true },
    'landmark-one-main': { enabled: true },
    'page-has-heading-one': { enabled: true },
    'region': { enabled: true },
    'skip-link': { enabled: true },
    'button-name': { enabled: true },
    'image-alt': { enabled: true },
    'label': { enabled: true },
    'list': { enabled: true },
    'listitem': { enabled: true },
    'definition-list': { enabled: true },
    'dlitem': { enabled: true },
    'frame-title': { enabled: true },
    'iframe-title': { enabled: true },
    'input-image-alt': { enabled: true },
    'object-alt': { enabled: true },
    'video-caption': { enabled: true },
    'video-description': { enabled: true },
    'aria-allowed-attr': { enabled: true },
    'aria-allowed-role': { enabled: true },
    'aria-command-name': { enabled: true },
    'aria-hidden-body': { enabled: true },
    'aria-hidden-focus': { enabled: true },
    'aria-input-field-name': { enabled: true },
    'aria-meter-name': { enabled: true },
    'aria-progressbar-name': { enabled: true },
    'aria-required-attr': { enabled: true },
    'aria-required-children': { enabled: true },
    'aria-required-parent': { enabled: true },
    'aria-roles': { enabled: true },
    'aria-toggle-field-name': { enabled: true },
    'aria-tooltip-name': { enabled: true },
    'aria-treeitem-name': { enabled: true },
    'aria-valid-attr': { enabled: true },
    'aria-valid-attr-value': { enabled: true },
    'aria-valid-role': { enabled: true },
    'button-name': { enabled: true },
    'bypass': { enabled: true },
    'checkboxgroup': { enabled: true },
    'duplicate-id': { enabled: true },
    'duplicate-id-active': { enabled: true },
    'duplicate-id-aria': { enabled: true },
    'form-field-multiple-labels': { enabled: true },
    'frame-focusable-content': { enabled: true },
    'frame-title-unique': { enabled: true },
    'heading-order': { enabled: true },
    'hidden-content': { enabled: true },
    'html-lang-valid': { enabled: true },
    'image-redundant-alt': { enabled: true },
    'label-content-name-mismatch': { enabled: true },
    'link-in-text-block': { enabled: true },
    'link-name': { enabled: true },
    'list': { enabled: true },
    'listitem': { enabled: true },
    'marquee': { enabled: true },
    'meta-refresh': { enabled: true },
    'meta-viewport': { enabled: true },
    'object-alt': { enabled: true },
    'radiogroup': { enabled: true },
    'region': { enabled: true },
    'scope-attr-valid': { enabled: true },
    'scrollable-region-focusable': { enabled: true },
    'select-name': { enabled: true },
    'server-side-image-map': { enabled: true },
    'svg-img-alt': { enabled: true },
    'td-headers-attr': { enabled: true },
    'th-has-data-cells': { enabled: true },
    'valid-lang': { enabled: true },
    'video-caption': { enabled: true },
    'video-description': { enabled: true },
  },
  // Set impact levels to include in results
  impact: ['critical', 'serious', 'moderate'],
  // Set timeout for async operations
  timeout: 1000,
  // Set element wait time
  waitForElement: 1000,
});

// Global accessibility testing utilities
global.a11yTestUtils = {
  // Test component accessibility
  testComponentAccessibility: async (component, options = {}) => {
    const { render } = await import('@testing-library/react');
    const { axe, toHaveNoViolations } = await import('jest-axe');

    const { container } = render(component);
    const results = await axe(container, options);

    expect(results).toHaveNoViolations();
    return results;
  },

  // Test page accessibility
  testPageAccessibility: async (page, options = {}) => {
    const { axe, toHaveNoViolations } = await import('jest-axe');

    const results = await axe(page, options);
    expect(results).toHaveNoViolations();
    return results;
  },

  // Test form accessibility
  testFormAccessibility: async (form, options = {}) => {
    const { axe, toHaveNoViolations } = await import('jest-axe');

    const results = await axe(form, {
      rules: {
        'label': { enabled: true },
        'form-field-multiple-labels': { enabled: true },
        'select-name': { enabled: true },
        'input-image-alt': { enabled: true },
        'aria-required-attr': { enabled: true },
        'aria-required-children': { enabled: true },
        'aria-required-parent': { enabled: true },
        'aria-valid-attr': { enabled: true },
        'aria-valid-attr-value': { enabled: true },
        'duplicate-id': { enabled: true },
        'duplicate-id-aria': { enabled: true },
      },
      ...options,
    });

    expect(results).toHaveNoViolations();
    return results;
  },

  // Test navigation accessibility
  testNavigationAccessibility: async (navigation, options = {}) => {
    const { axe, toHaveNoViolations } = await import('jest-axe');

    const results = await axe(navigation, {
      rules: {
        'landmark-one-main': { enabled: true },
        'region': { enabled: true },
        'skip-link': { enabled: true },
        'bypass': { enabled: true },
        'link-name': { enabled: true },
        'list': { enabled: true },
        'listitem': { enabled: true },
        'heading-order': { enabled: true },
      },
      ...options,
    });

    expect(results).toHaveNoViolations();
    return results;
  },

  // Test keyboard navigation
  testKeyboardNavigation: async (container) => {
    const { screen, fireEvent } = await import('@testing-library/react');

    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    const tabOrder = [];

    // Test tab navigation
    for (let i = 0; i < focusableElements.length; i++) {
      fireEvent.keyDown(container, { key: 'Tab' });
      const activeElement = document.activeElement;
      tabOrder.push(activeElement);
    }

    return {
      focusableCount: focusableElements.length,
      tabOrder,
      isAccessible: tabOrder.length === focusableElements.length,
    };
  },

  // Test screen reader compatibility
  testScreenReaderCompatibility: async (container) => {
    const { axe, toHaveNoViolations } = await import('jest-axe');

    const results = await axe(container, {
      rules: {
        'aria-allowed-attr': { enabled: true },
        'aria-allowed-role': { enabled: true },
        'aria-command-name': { enabled: true },
        'aria-hidden-body': { enabled: true },
        'aria-hidden-focus': { enabled: true },
        'aria-input-field-name': { enabled: true },
        'aria-required-attr': { enabled: true },
        'aria-required-children': { enabled: true },
        'aria-required-parent': { enabled: true },
        'aria-roles': { enabled: true },
        'aria-valid-attr': { enabled: true },
        'aria-valid-attr-value': { enabled: true },
        'aria-valid-role': { enabled: true },
        'button-name': { enabled: true },
        'image-alt': { enabled: true },
        'label': { enabled: true },
        'link-name': { enabled: true },
        'select-name': { enabled: true },
      },
    });

    expect(results).toHaveNoViolations();
    return results;
  },

  // Test color contrast
  testColorContrast: async (container) => {
    const { axe, toHaveNoViolations } = await import('jest-axe');

    const results = await axe(container, {
      rules: {
        'color-contrast': { enabled: true },
      },
    });

    expect(results).toHaveNoViolations();
    return results;
  },

  // Test focus management
  testFocusManagement: async (container) => {
    const { fireEvent } = await import('@testing-library/react');

    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    const focusResults = [];

    for (const element of focusableElements) {
      element.focus();
      const isFocused = document.activeElement === element;
      focusResults.push({
        element,
        isFocused,
        hasFocusVisible: element.classList.contains('focus-visible'),
      });
    }

    return {
      totalElements: focusableElements.length,
      focusedElements: focusResults.filter(r => r.isFocused).length,
      focusResults,
    };
  },
};

// Custom matchers for accessibility testing
expect.extend({
  toBeAccessible(received) {
    const pass = received.violations.length === 0;
    if (pass) {
      return {
        message: () => `expected component to be accessible`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected component to be accessible, but found ${received.violations.length} violations`,
        pass: false,
      };
    }
  },

  toHaveProperHeadingStructure(received) {
    const headings = received.querySelectorAll('h1, h2, h3, h4, h5, h6');
    const levels = Array.from(headings).map(h => parseInt(h.tagName.charAt(1)));

    let pass = true;
    for (let i = 1; i < levels.length; i++) {
      if (levels[i] - levels[i - 1] > 1) {
        pass = false;
        break;
      }
    }

    if (pass) {
      return {
        message: () => `expected proper heading structure`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected proper heading structure, but found skipped levels`,
        pass: false,
      };
    }
  },

  toHaveKeyboardNavigation(received) {
    const focusableElements = received.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    const pass = focusableElements.length > 0;

    if (pass) {
      return {
        message: () => `expected keyboard navigation to be available`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected keyboard navigation to be available, but no focusable elements found`,
        pass: false,
      };
    }
  },
});
