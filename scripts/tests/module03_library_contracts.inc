Library library;
library.add_item(std::make_unique<PrintedBook>("A","Alpha",7));
library.add_member(Member{"M","Member"});
auto rejected = [](auto action) {
    bool caught=false;
    try { action(); } catch (const std::exception&) { caught=true; }
    assert(caught);
};
rejected([&]{library.add_item(nullptr);});
rejected([&]{library.add_item(std::make_unique<PrintedBook>("A","Duplicate",7));});
rejected([&]{library.add_member(Member{"M","Duplicate"});});
rejected([&]{library.borrow("A","missing");});
rejected([&]{library.borrow("missing","M");});
library.borrow("A","M");
rejected([&]{library.borrow("A","M");});
library.save_report("on-loan.txt");
{
    std::ifstream file{"on-loan.txt"};
    std::string line;
    assert(std::getline(file,line));
    assert(line=="A,Alpha,on-loan,7");
    assert(!std::getline(file,line));
}
library.return_item("A");
rejected([&]{library.return_item("A");});
library.borrow("A","M");
library.return_item("A");
rejected([&]{library.save_report("missing-dir/report");});
library.save_report("after-error.txt");
{
    std::ifstream file{"after-error.txt"};
    std::string line;
    assert(std::getline(file,line));
    assert(line=="A,Alpha,available,7");
}
