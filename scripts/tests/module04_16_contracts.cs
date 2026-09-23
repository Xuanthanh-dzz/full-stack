using TaskManager.Domain;
using TaskManager.Application;
internal static class Contracts
{
 static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
 public static void Main(){
var repository=new FakeRepository();var service=new TodoService(repository);service.Add("A");var before=service.GetAll();
repository.Fail=true;Throws<IOException>(()=>service.Add("B"));Check(service.GetAll().Count==1,"failed add changed list");
Throws<IOException>(()=>service.MarkCompleted(1));Check(service.GetAll()[0].Status==TodoStatus.Pending,"failed completion changed shared item");
Throws<IOException>(()=>service.Remove(1));Check(service.GetAll().Count==1,"failed remove");
repository.Fail=false;Check(service.MarkCompleted(1),"complete");Check(before[0].Status==TodoStatus.Pending,"old snapshot changed");
Check(service.GetAll()[0].Status==TodoStatus.Completed,"new snapshot");Check(!service.Remove(999),"missing ID");
var item=new TodoItem(2," X ",TodoStatus.Pending,new DateTimeOffset(2026,1,1,7,0,0,TimeSpan.FromHours(7)));
Check(item.CreatedAt.Offset==TimeSpan.Zero&&item.CreatedAt.Hour==0&&item.Title=="X","UTC normalize");
 }
}
internal sealed class FakeRepository:ITodoRepository
{
 public bool Fail;
 public List<TodoItem> Load()=>[];
 public void Save(IReadOnlyCollection<TodoItem> items){if(Fail)throw new IOException("injected before persistence");}
}
