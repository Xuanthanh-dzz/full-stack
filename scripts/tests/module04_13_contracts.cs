using CollectionDemo;
internal static class Contracts
{
 static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
 public static void Main(){
var codes=new[]{new ProductCode(" a ")};var first=new Order("1",codes);codes[0]=new ProductCode("changed");
Check(first.ProductCodes[0].Value=="A","input collection clone");var w=new Warehouse();Check(w.Register(first),"first");
Check(!w.Register(new Order("1",[new ProductCode("B")])),"duplicate");Check(w.Orders.Count==1&&w.PendingCount==1&&w.UniqueProductCount==1,"duplicate changed indexes");
w.Register(new Order("2",[new ProductCode("a")]));Check(w.UniqueProductCount==1,"hash equality");Check(w.TryProcessNext(out var processed)&&ReferenceEquals(processed,first),"FIFO");
Check(w.TryUndoLastProcessing()&&first.Status==OrderStatus.Pending,"undo");Check(w.TryProcessNext(out processed)&&processed!.Id=="2","undo queued at tail");
Check(w.TryProcessNext(out processed)&&processed!.Id=="1","next");Check(!w.TryProcessNext(out processed)&&processed is null,"empty queue");
 }
}
