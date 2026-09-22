using GenericsDemo;
internal static class Contracts
{
static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
static void Throws<T>(Action action) where T:Exception{try{action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
static async Task ThrowsAsync<T>(Func<Task> action) where T:Exception{try{await action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
public static void Main(){
var s=new EntityStore<string,Product>(StringComparer.OrdinalIgnoreCase);var p=new Product(" a ","A",1m,2);s.Add(p);
Check(ReferenceEquals(s.GetRequired("a"),p),"lookup identity");Throws<InvalidOperationException>(()=>s.Add(new Product("A","B",2,3)));Check(s.Count==1,"duplicate mutated store");
Throws<KeyNotFoundException>(()=>s.GetRequired("B"));Check(GenericAlgorithms.GreaterOf(4,4)==4,"tie");
}
}
