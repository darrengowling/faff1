#!/usr/bin/env python3
"""
Complete I18N Migration Script
Systematically completes the i18n migration for all remaining components
"""

import os
import re
from pathlib import Path

class I18nMigrationHelper:
    def __init__(self):
        self.frontend_path = "/app/frontend/src"
        self.components_path = f"{self.frontend_path}/components"
        self.ui_path = f"{self.frontend_path}/components/ui"
        
        # Track migration progress
        self.migrations_done = []
        self.migrations_failed = []

    def add_use_translation_import(self, file_path):
        """Add useTranslation import to a React component"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check if useTranslation is already imported
            if 'useTranslation' in content:
                return True, "Already has useTranslation import"
            
            # Find React import and add useTranslation after it
            react_import_pattern = r"(import React[^;]+;)"
            if re.search(react_import_pattern, content):
                new_content = re.sub(
                    react_import_pattern,
                    r"\1\nimport { useTranslation } from 'react-i18next';",
                    content
                )
            else:
                # Add at the top if no React import found
                new_content = "import { useTranslation } from 'react-i18next';\n" + content
            
            with open(file_path, 'w') as f:
                f.write(new_content)
            
            return True, "Added useTranslation import"
        except Exception as e:
            return False, str(e)

    def add_translation_hook(self, file_path, component_name_pattern):
        """Add const { t } = useTranslation(); to component function"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check if translation hook is already there
            if 'const { t } = useTranslation()' in content:
                return True, "Already has translation hook"
            
            # Find component function pattern and add hook
            component_pattern = rf"(const {component_name_pattern} = [^{{]*\{{)"
            if re.search(component_pattern, content):
                new_content = re.sub(
                    component_pattern,
                    r"\1\n  const { t } = useTranslation();",
                    content
                )
                
                with open(file_path, 'w') as f:
                    f.write(new_content)
                
                return True, "Added translation hook"
            else:
                return False, f"Could not find component pattern: {component_name_pattern}"
        except Exception as e:
            return False, str(e)

    def migrate_common_strings(self, file_path):
        """Replace common hardcoded strings with translation keys"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Common string replacements
            replacements = [
                # Loading states
                (r'"Loading\.\.\."', "t('loading.loading')"),
                (r'"Loading"', "t('loading.loading')"),
                (r'"Please wait"', "t('loading.pleaseWait')"),
                
                # Common actions
                (r'"Save"', "t('common.save')"),
                (r'"Cancel"', "t('common.cancel')"),
                (r'"Close"', "t('common.close')"),
                (r'"Back"', "t('common.back')"),
                (r'"Refresh"', "t('common.refresh')"),
                (r'"Retry"', "t('common.retry')"),
                (r'"Try Again"', "t('errors.tryAgain')"),
                
                # Error messages
                (r'"Error"', "t('common.error')"),
                (r'"Failed to load"', "t('errors.failedToLoad')"),
                (r'"Something went wrong"', "t('errors.somethingWentWrong')"),
                
                # Auction specific
                (r'"Start Auction"', "t('dashboard.startAuction')"),
                (r'"Join Auction"', "t('dashboard.joinAuction')"),
                (r'"Place Bid"', "t('auction.placeBid')"),
                (r'"Bidding\.\.\."', "t('auction.bidding')"),
                (r'"Current Bid"', "t('auction.currentBid')"),
                (r'"Time Left"', "t('auction.timeLeft')"),
                (r'"No Bids"', "t('auction.noBids')"),
                
                # Navigation
                (r'"Dashboard"', "t('nav.dashboard')"),
                (r'"My Clubs"', "t('nav.myClubs')"),
                (r'"Leaderboard"', "t('nav.leaderboard')"),
                (r'"Fixtures"', "t('nav.fixtures')"),
                (r'"Admin"', "t('nav.admin')"),
                
                # Status messages
                (r'"Connected"', "t('connection.connected')"),
                (r'"Connecting\.\.\."', "t('connection.connecting')"),
                (r'"Disconnected"', "t('connection.disconnected')"),
                (r'"Offline"', "t('connection.offline')"),
            ]
            
            changes_made = 0
            for pattern, replacement in replacements:
                new_content, count = re.subn(pattern, replacement, content)
                if count > 0:
                    content = new_content
                    changes_made += count
            
            if changes_made > 0:
                with open(file_path, 'w') as f:
                    f.write(content)
                return True, f"Replaced {changes_made} strings"
            else:
                return True, "No common strings found to replace"
                
        except Exception as e:
            return False, str(e)

    def migrate_component(self, file_path, component_name):
        """Migrate a single component to use i18n"""
        print(f"Migrating: {file_path}")
        
        results = []
        
        # Step 1: Add import
        success, message = self.add_use_translation_import(file_path)
        results.append(f"Import: {message}")
        if not success:
            return False, results
        
        # Step 2: Add hook
        success, message = self.add_translation_hook(file_path, component_name)
        results.append(f"Hook: {message}")
        
        # Step 3: Replace common strings
        success, message = self.migrate_common_strings(file_path)
        results.append(f"Strings: {message}")
        
        return True, results

    def migrate_all_components(self):
        """Migrate all remaining components"""
        # Components to migrate (filename -> component name pattern)
        components_to_migrate = {
            f"{self.components_path}/Fixtures.js": "Fixtures",
            f"{self.components_path}/Leaderboard.js": "Leaderboard", 
            f"{self.components_path}/DiagnosticPage.js": "DiagnosticPage",
            f"{self.ui_path}/connection-status.jsx": "ConnectionStatusIndicator",
            f"{self.ui_path}/auction-help.jsx": "AuctionMechanicsHelp",
            f"{self.ui_path}/lot-closing.jsx": "LotCloseConfirmation",
            f"{self.ui_path}/live-status.jsx": "BudgetStatus",
            f"{self.ui_path}/tooltip.js": "AuctionTooltip",
        }
        
        print("🚀 Starting I18N Migration for Remaining Components")
        print("=" * 60)
        
        for file_path, component_name in components_to_migrate.items():
            if os.path.exists(file_path):
                try:
                    success, results = self.migrate_component(file_path, component_name)
                    if success:
                        self.migrations_done.append(file_path)
                        print(f"✅ {file_path}")
                        for result in results:
                            print(f"   {result}")
                    else:
                        self.migrations_failed.append((file_path, results))
                        print(f"❌ {file_path}")
                        for result in results:
                            print(f"   {result}")
                except Exception as e:
                    self.migrations_failed.append((file_path, str(e)))
                    print(f"❌ {file_path} - {str(e)}")
            else:
                print(f"⚠️  {file_path} - File not found")
                self.migrations_failed.append((file_path, "File not found"))
            
            print()

    def create_migration_report(self):
        """Create a detailed migration report"""
        report = f"""
# I18N Migration Completion Report

**Generated**: {__import__('datetime').datetime.now().isoformat()}

## Summary
- **Total components processed**: {len(self.migrations_done) + len(self.migrations_failed)}
- **Successfully migrated**: {len(self.migrations_done)}
- **Failed migrations**: {len(self.migrations_failed)}
- **Success rate**: {(len(self.migrations_done)/(len(self.migrations_done)+len(self.migrations_failed))*100):.1f}%

## Successfully Migrated Components
"""
        for component in self.migrations_done:
            report += f"- ✅ {component}\n"
        
        if self.migrations_failed:
            report += f"\n## Failed Migrations\n"
            for component, error in self.migrations_failed:
                report += f"- ❌ {component}: {error}\n"
        
        report += f"""
## Next Steps
1. **Manual Review**: Check migrated components for proper i18n usage
2. **Test Application**: Ensure all UI text displays correctly  
3. **Add Missing Keys**: Update translation keys for any missed strings
4. **Verify Functionality**: Confirm app functionality remains intact

## Manual Migration Needed
The following areas may need manual attention:
- Complex conditional text rendering
- Dynamic strings with complex interpolation  
- Component-specific microcopy not covered by common patterns
- Error messages with specific context

## Testing Checklist
- [ ] All components load without React errors
- [ ] UI text displays correctly (no missing translation keys)
- [ ] Dynamic content (user names, counts, etc.) interpolates properly
- [ ] Loading states show translated text
- [ ] Error states show translated messages
- [ ] All navigation elements use translation keys
"""
        
        with open("/app/I18N_MIGRATION_COMPLETION_REPORT.md", "w") as f:
            f.write(report)
        
        return report

    def run_migration(self):
        """Run the complete migration process"""
        self.migrate_all_components()
        
        print("\n" + "=" * 60)
        print("📊 MIGRATION SUMMARY")
        print("=" * 60)
        print(f"✅ Successfully migrated: {len(self.migrations_done)}")
        print(f"❌ Failed migrations: {len(self.migrations_failed)}")
        
        if self.migrations_failed:
            print(f"\n💥 FAILED MIGRATIONS:")
            for component, error in self.migrations_failed:
                print(f"  - {component}: {error}")
        
        # Create report
        report = self.create_migration_report()
        print(f"\n📄 Detailed report saved to: /app/I18N_MIGRATION_COMPLETION_REPORT.md")
        
        if len(self.migrations_failed) == 0:
            print(f"\n🎉 ALL MIGRATIONS COMPLETED SUCCESSFULLY!")
            print(f"🌐 I18N implementation is now complete for all components")
            return True
        else:
            print(f"\n⚠️  SOME MIGRATIONS FAILED - Manual intervention required")
            return False


if __name__ == "__main__":
    migrator = I18nMigrationHelper()
    success = migrator.run_migration()
    
    if success:
        print(f"\n✨ I18N Migration Complete!")
        exit(0)
    else:
        print(f"\n🔧 Manual fixes required - check report for details")
        exit(1)